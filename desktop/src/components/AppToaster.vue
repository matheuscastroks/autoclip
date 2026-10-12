<script setup lang="ts">
import {onMounted,onUnmounted,shallowRef} from 'vue'
import {Toaster} from 'vue-sonner'
import 'vue-sonner/style.css'
// Native dialogs occupy the browser top layer. Move the same host inside the open dialog.
const target=shallowRef<HTMLElement|string>('body')
let observer:MutationObserver|undefined
function syncTarget(){target.value=Array.from(document.querySelectorAll<HTMLDialogElement>('dialog[open]')).at(-1)||document.body}
onMounted(()=>{syncTarget();observer=new MutationObserver(syncTarget);observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['open']})})
onUnmounted(()=>observer?.disconnect())
</script>
<template><Teleport :to="target"><Toaster data-slot="app-toaster" position="top-center" theme="light" :style="{'--width':'420px'}" :visible-toasts="3" :expand="true" :close-button="true" :offset="20" :mobile-offset="12" container-aria-label="Avisos do aplicativo" :hotkey="['altKey','KeyT']" :toast-options="{class:'app-toast',closeButtonAriaLabel:'Fechar aviso'}"/></Teleport></template>
<style>
[data-sonner-toaster]{z-index:10000;font-family:inherit}
[data-sonner-toaster] [data-sonner-toast].app-toast{background:var(--panel);color:var(--ink);border:2px solid var(--ink);border-left:6px solid var(--accent);border-radius:0;box-shadow:4px 4px 0 var(--ink);padding:17px 38px 17px 17px;gap:12px}
[data-sonner-toaster] [data-sonner-toast].app-toast [data-title]{font-size:14px;font-weight:700;line-height:1.5}
[data-sonner-toaster] [data-sonner-toast].app-toast [data-description]{font-size:12px;line-height:1.6;color:var(--muted);overflow-wrap:anywhere}
[data-sonner-toaster] [data-sonner-toast].app-toast [data-icon]{color:var(--accent)}
[data-sonner-toaster] [data-sonner-toast].app-toast[data-type=error]{border-left-color:#a72d24}
[data-sonner-toaster] [data-sonner-toast].app-toast[data-type=error] [data-icon]{color:#a72d24}
[data-sonner-toaster] [data-sonner-toast].app-toast [data-close-button]{border-radius:0;border:1px solid var(--ink);color:var(--ink);background:var(--panel)}
[data-sonner-toaster] [data-close-button]:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(prefers-reduced-motion:reduce){[data-sonner-toast]{transition:none!important;animation:none!important}}
</style>
