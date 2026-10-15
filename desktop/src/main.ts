import { createApp } from 'vue';
import App from './App.vue';
import { initializeSession } from './api';
import 'element-plus/theme-chalk/index.css';
import './tokens.css';
import './element-theme.css';
import './layouts.css';
import './theme.css';
import './desktop.css';

initializeSession();
createApp(App).mount('#app');
