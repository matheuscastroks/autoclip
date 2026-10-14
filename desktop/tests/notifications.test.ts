import {describe,it,expect,vi,beforeEach} from 'vitest'

const mockNotification = vi.fn()
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    ElNotification: (...args: unknown[]) => mockNotification(...args),
  }
})

import {notify,notifyJob,createJobNotifier,resetNotifications} from '../src/notifications'

const job={id:'j',project_id:'p',operation:'prepare',status:'failed',created_at:'',requests_used:0,request_limit:null,events:[],error:{code:'SOURCE_AUTH_REQUIRED',message:'O YouTube bloqueou o download.'}}

beforeEach(()=>{vi.clearAllMocks();resetNotifications()})

describe('single notification channel with ElNotification',()=>{
 it('does not repeat a job error on each poll but permits explicit details',()=>{
  notifyJob(job);notifyJob({...job});notifyJob({...job,requests_used:2})
  expect(mockNotification).toHaveBeenCalledTimes(1)
  notifyJob(job,true);expect(mockNotification).toHaveBeenCalledTimes(2)
 })
 it('ignores old history at startup and notifies terminal transitions once',()=>{
  const observe=createJobNotifier();observe([job]);expect(mockNotification).not.toHaveBeenCalled()
  observe([{...job,id:'new',status:'running'}]);observe([{...job,id:'new'}]);observe([{...job,id:'new'}])
  expect(mockNotification).toHaveBeenCalledTimes(1)
 })
 it('reports partial preview failure even when a ready preview is reusable',()=>{
  const observe=createJobNotifier();observe([]);observe([{...job,operation:'render'}])
  expect(mockNotification).toHaveBeenCalledWith(expect.objectContaining({
    type: 'error',
    message: expect.stringContaining(job.error.message)
  }))
 })
 it('uses finite error durations and deduplicates a polling connectivity failure',()=>{
  notify.error('Sem conexão',{key:'connection'});notify.error('Sem conexão',{key:'connection'})
  expect(mockNotification).toHaveBeenCalledTimes(1)
  expect(mockNotification).toHaveBeenCalledWith(expect.objectContaining({
    type: 'error',
    duration: 9000
  }))
 })
 it('announces an individual cut failure immediately while the batch keeps running',()=>{
  const observe=createJobNotifier();observe([])
  const batch={...job,status:'running',operation:'render',progress:{stage:'render',steps:{},items:[{candidate_id:'cut',title:'Trecho um',state:'failed',phase:'failed',processed_us:0,total_us:null,error_code:'RENDER_FAILED'}]}}
  observe([batch]);observe([batch])
  expect(mockNotification).toHaveBeenCalledTimes(1)
  expect(mockNotification).toHaveBeenCalledWith(expect.objectContaining({
    type: 'error',
    message: expect.stringContaining('Trecho um')
  }))
 })
})
