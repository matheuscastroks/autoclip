<script setup lang="ts">
import {computed} from 'vue'
import {Check,ChevronDown,ChevronUp} from '@lucide/vue'
import {SelectRoot,SelectTrigger,SelectPortal,SelectContent,SelectViewport,SelectItem,SelectItemText,SelectItemIndicator,SelectScrollUpButton,SelectScrollDownButton} from 'reka-ui'
defineOptions({inheritAttrs:false})
const props=withDefaults(defineProps<{modelValue:string;options:{value:string;label:string;disabled?:boolean}[];label:string;disabled?:boolean;required?:boolean}>(),{disabled:false,required:false})
const emit=defineEmits<{'update:modelValue':[value:string]}>()
const selected=computed(()=>props.options.find(o=>o.value===props.modelValue)?.label||props.modelValue||'Selecione uma opção')
function update(value:unknown){if(typeof value==='string')emit('update:modelValue',value)}
</script>
<template>
 <SelectRoot :model-value="modelValue" :disabled="disabled" :required="required" @update:model-value="update">
  <SelectTrigger v-bind="$attrs" data-slot="select-trigger" class="app-select-trigger ui-control" :aria-label="label" type="button"><span>{{selected}}</span><ChevronDown :size="17" aria-hidden="true"/></SelectTrigger>
  <SelectPortal><SelectContent class="app-select-content" position="popper" :side-offset="8" :collision-padding="12" :body-lock="false">
   <SelectScrollUpButton class="app-select-scroll" aria-label="Opções anteriores"><ChevronUp :size="16"/></SelectScrollUpButton>
   <SelectViewport class="app-select-viewport"><SelectItem v-for="option in options" :key="option.value" :value="option.value" :disabled="option.disabled" class="app-select-item" :text-value="option.label"><SelectItemText>{{option.label}}</SelectItemText><SelectItemIndicator class="app-select-check"><Check :size="16" aria-hidden="true"/></SelectItemIndicator></SelectItem></SelectViewport>
   <SelectScrollDownButton class="app-select-scroll" aria-label="Mais opções"><ChevronDown :size="16"/></SelectScrollDownButton>
  </SelectContent></SelectPortal>
 </SelectRoot>
</template>
