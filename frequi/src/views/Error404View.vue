<template>
  <div class="ft-container">
    <FtPanel>
      <FtEmpty title="404 - page not found" text="The page you are looking for does not exist.">
        <template #actions>
          <RouterLink to="/">Back to the overview</RouterLink>
        </template>
      </FtEmpty>
    </FtPanel>
  </div>
</template>
