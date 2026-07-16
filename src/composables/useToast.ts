import { reactive } from 'vue'

const state = reactive({
  visible: false,
  message: '',
  timer: 0,
})

export function useToast() {
  function show(message: string, duration = 2000) {
    clearTimeout(state.timer)
    state.message = message
    state.visible = true
    state.timer = window.setTimeout(() => {
      state.visible = false
    }, duration)
  }
  return { ...state, show }
}
