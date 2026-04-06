/**
 * @vitest-environment jsdom
 */

import { defineComponent, h, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import KonvaCanvasStage from '@/components/canvas/KonvaCanvasStage.vue'

const pointerState = { x: 180, y: 140 }
const stageNode = {
  x: () => 0,
  y: () => 0,
  scaleX: () => 1,
  getPointerPosition: () => ({ ...pointerState }),
  draggable: vi.fn(),
  batchDraw: vi.fn()
}

const VStageStub = defineComponent({
  name: 'VStageStub',
  emits: ['wheel', 'dragmove', 'dragend', 'mousedown', 'mousemove', 'mouseup', 'click'],
  setup(_, { emit, slots }) {
    return {
      stageSlots: slots,
      getNode() {
        return stageNode
      },
      emitKonva(name, detail) {
        emit(name, detail)
      }
    }
  },
  render() {
    return h(
      'div',
      {
        class: 'v-stage-stub',
        onMousedown: (event) => this.emitKonva('mousedown', event.detail),
        onMousemove: (event) => this.emitKonva('mousemove', event.detail),
        onMouseup: (event) => this.emitKonva('mouseup', event.detail),
        onClick: (event) => this.emitKonva('click', event.detail)
      },
      this.stageSlots?.default?.()
    )
  }
})

const passthroughStub = (name) =>
  defineComponent({
    name,
    setup(_, { slots }) {
      return () => h('div', { class: `${name}-stub` }, slots.default?.())
    }
  })

const mountStage = () =>
  mount(KonvaCanvasStage, {
    props: {
      items: [],
      connections: [],
      selectedItemIds: [],
      selectedConnectionIds: [],
      editingItemId: ''
    },
    global: {
      stubs: {
        'v-stage': VStageStub,
        'v-layer': passthroughStub('v-layer'),
        'v-group': passthroughStub('v-group'),
        'v-rect': passthroughStub('v-rect'),
        'v-image': passthroughStub('v-image'),
        'v-text': passthroughStub('v-text'),
        'v-line': passthroughStub('v-line'),
        'v-circle': passthroughStub('v-circle'),
        CanvasGeneratingOverlay: true
      }
    }
  })

describe('KonvaCanvasStage marquee vs pan behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.ResizeObserver = class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
      x: 0,
      y: 0,
      top: 0,
      left: 0,
      right: 800,
      bottom: 600,
      width: 800,
      height: 600,
      toJSON() {}
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('only starts marquee selection when shift is held on empty stage', async () => {
    const wrapper = mountStage()
    await nextTick()

    const stage = wrapper.get('.v-stage-stub')
    stage.element.dispatchEvent(
      new CustomEvent('mousedown', {
        bubbles: true,
        detail: {
          target: stageNode,
          evt: { button: 0, shiftKey: true, preventDefault: vi.fn() }
        }
      })
    )
    pointerState.x = 260
    pointerState.y = 220
    stage.element.dispatchEvent(
      new CustomEvent('mousemove', {
        bubbles: true,
        detail: { target: stageNode, evt: {} }
      })
    )
    stage.element.dispatchEvent(
      new CustomEvent('mouseup', {
        bubbles: true,
        detail: { target: stageNode, evt: {} }
      })
    )

    expect(wrapper.emitted('selection-box-end')).toHaveLength(1)
    expect(stageNode.draggable).toHaveBeenCalledWith(false)
    expect(stageNode.draggable).toHaveBeenLastCalledWith(true)
    wrapper.unmount()
  })

  it('keeps the stage draggable on plain left drag without creating a marquee', async () => {
    const wrapper = mountStage()
    await nextTick()

    const stage = wrapper.get('.v-stage-stub')
    stage.element.dispatchEvent(
      new CustomEvent('mousedown', {
        bubbles: true,
        detail: {
          target: stageNode,
          evt: { button: 0, shiftKey: false, preventDefault: vi.fn() }
        }
      })
    )
    stage.element.dispatchEvent(
      new CustomEvent('mouseup', {
        bubbles: true,
        detail: { target: stageNode, evt: {} }
      })
    )

    expect(wrapper.emitted('selection-box-end')).toBeFalsy()
    expect(stageNode.draggable).not.toHaveBeenCalledWith(false)
    wrapper.unmount()
  })
})
