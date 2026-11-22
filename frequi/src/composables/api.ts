import type { AxiosHeaders, InternalAxiosRequestConfig } from 'axios';
import axios from 'axios';

type UserServiceType = ReturnType<typeof useLoginInfo>;

export function useApi(userService: UserServiceType, botId: string) {
  const api = axios.create({
    baseURL: userService.baseUrl.value,
    timeout: 20000,
    withCredentials: true,
  });
  // Sent auth headers interceptor
  api.interceptors.request.use(
    (request) => {
      const token = userService.accessToken.value;
      try {
        if (token) {
          request.headers = request.headers as AxiosHeaders;
          // Append token to each request
          request.headers.set('Authorization', `Bearer ${token}`);
        }
      } catch (e) {
        console.log(e);
      }
      return request;
    },
    (error) => Promise.reject(error),
  );

  api.interceptors.response.use(
    (response) => response,
    (err) => {
      // console.log(err);
      const config = err.config as
        | (InternalAxiosRequestConfig & { _ftRetried?: boolean })
        | undefined;
      if (err.response && err.response.status === 401 && config && !config._ftRetried) {
        // Access token expired: refresh it once, then repeat the request with the new token.
        return userService.refreshToken().then(
          () => api.request({ ...config, _ftRetried: true } as InternalAxiosRequestConfig),
          (error) => {
            console.log('No new token received', error);
            const botStore = useBotStore();
            if (botStore.botStores[botId]) {
              botStore.botStores[botId].setIsBotOnline(false);
              botStore.botStores[botId].isBotLoggedIn = false;
            }
            return Promise.reject(err);
          },
        );
      }
      if ((err.response && err.response.status === 500) || err.message === 'Network Error') {
        console.log('Bot not running...');
        const botStore = useBotStore();
        botStore.botStores[botId]?.setIsBotOnline(false);
      }

      return new Promise((resolve, reject) => {
        reject(err);
      });
    },
  );

  return {
    api,
  };
}
