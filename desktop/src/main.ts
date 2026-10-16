import { createApp } from 'vue';
import App from './App.vue';
import { initializeSession } from './api';
import { applyTheme, theme } from './composables/useTheme';
import 'element-plus/theme-chalk/index.css';
import './tokens.css';
import './element-theme.css';
import './layouts.css';
import './theme.css';
import './desktop.css';

initializeSession();
applyTheme(theme.value);
createApp(App).mount('#app');
