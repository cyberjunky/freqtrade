import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';

import App from './App.vue';
import router from './router';

import { PrimeVue, FtTheme, ToastService } from './plugins/primevue';
import { registerFtEchartsThemes } from './plugins/echartsTheme';

// Styles are loaded (imported by plugins/primevue) - build the chart themes from the tokens.
registerFtEchartsThemes();

const myApp = createApp(App);

const pinia = createPinia();
pinia.use(piniaPluginPersistedstate);
myApp.use(pinia);

myApp.use(PrimeVue, {
  theme: {
    preset: FtTheme,
    options: {
      darkModeSelector: '.ft-dark-theme',
      cssLayer: {
        name: 'primevue',
        order: 'theme, base, primevue',
      },
    },
  },
});
myApp.use(ToastService);

myApp.use(router);

myApp.mount('#app');
