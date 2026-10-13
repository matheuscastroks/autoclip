import {mount} from '@vue/test-utils'
import {describe,it,expect} from 'vitest'
import ReviewPanel from '../src/components/ReviewPanel.vue'
import type {Job,Revision} from '../src/types'

describe('cut deletion during processing',()=>{
  for(const operation of ['analyze','transcribe','render','export','prepare','import']){
    it(operation,()=>{
      const blocked=!['analyze','transcribe'].includes(operation)
      const wrapper=mount(ReviewPanel,{props:{revisions:[{revision_id:'cut',title:'Corte',technical_pass:true,warnings:[],review_status:'needs_review'} as unknown as Revision],manual:false,mediaUrl:'',sourceUrl:'',processing:true,jobs:[{id:'job',operation,status:'running'} as Job]}})
      expect((wrapper.get('[data-action="delete-clip"]').element as HTMLButtonElement).disabled).toBe(blocked)
      expect(wrapper.find('#delete-blocked-reason').exists()).toBe(blocked)
      wrapper.unmount()
    })
  }
})
