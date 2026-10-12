import {createApp} from 'vue'
import App from './App.vue'
import {initializeSession} from './api'
import './styles.css'
initializeSession();createApp(App).mount('#app')
