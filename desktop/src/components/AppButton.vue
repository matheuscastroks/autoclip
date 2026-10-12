<script setup lang="ts">
// Native attributes and listeners fall through once to the actual control.
defineOptions({inheritAttrs:true})
</script>
<template><button class="physical-control"><slot/></button></template>
