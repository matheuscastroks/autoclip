import {createApp} from 'vue'
import App from './App.vue'
import {initializeSession} from './api'
import './tokens.css'
import './layouts.css'
import './theme.css'
initializeSession();createApp(App).mount('#app')
