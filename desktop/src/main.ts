import {createApp} from 'vue'
import App from './App.vue'
import {initializeSession} from './api'
import './styles.css'
import './brutalist.css'
import './desktop-polish.css'
initializeSession();createApp(App).mount('#app')
