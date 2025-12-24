import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import { useCharacterWorkflow } from './useCharacterWorkflow'
import { useSceneWorkflow } from './useSceneWorkflow'
import { useShotWorkflow } from './useShotWorkflow'
import { useTransitionWorkflow } from './useTransitionWorkflow'

export function useMovieWorkflow() {
    const route = useRoute()
    const router = useRouter()

    const selectedChapterId = ref(route.params.chapterId || null)
    // 从route.params获取projectId（路由中定义的参数）
    const projectId = ref(route.params.projectId || null)
    const currentStep = ref(0)
    const loading = ref(false)

    console.log('useMovieWorkflow init:', {
        chapterId: selectedChapterId.value,
        projectId: projectId.value,
        routeParams: route.params
    })

    // Initialize workflows
    const characterWorkflow = useCharacterWorkflow(projectId, api)
    const sceneWorkflow = useSceneWorkflow(api)
    const shotWorkflow = useShotWorkflow(sceneWorkflow.script, api)
    const transitionWorkflow = useTransitionWorkflow(api)

    // Computed states
    const canExtractScenes = computed(() => {
        return characterWorkflow.characters.value.length > 0
    })

    const canExtractShots = computed(() => {
        return sceneWorkflow.script.value?.scenes?.length > 0
    })

    const canGenerateKeyframes = computed(() => {
        return shotWorkflow.allShots.value.length > 0 &&
            characterWorkflow.characters.value.every(c => c.avatar_url)
    })

    const canCreateTransitions = computed(() => {
        return shotWorkflow.allShots.value.every(s => s.keyframe_url)
    })

    const canGenerateTransitionVideos = computed(() => {
        return transitionWorkflow.transitions.value.length > 0
    })

    // Auto-determine current step based on data
    const determineCurrentStep = () => {
        if (!sceneWorkflow.script.value) {
            currentStep.value = 0 // Characters
        } else if (!sceneWorkflow.script.value.scenes?.length) {
            currentStep.value = 1 // Scenes
        } else if (!shotWorkflow.allShots.value.length) {
            currentStep.value = 2 // Shots
        } else if (!shotWorkflow.allShots.value.every(s => s.keyframe_url)) {
            currentStep.value = 3 // Keyframes
        } else if (!transitionWorkflow.transitions.value.length) {
            currentStep.value = 4 // Transitions
        } else {
            currentStep.value = 5 // Final
        }
    }

    // Load initial data (only characters, not script)
    const loadData = async () => {
        if (!selectedChapterId.value || !projectId.value) {
            console.warn('Cannot load data: missing chapterId or projectId')
            return
        }

        loading.value = true
        try {
            // Only load characters initially
            await characterWorkflow.loadCharacters()

            // Try to load script if it exists, but don't fail if it doesn't
            try {
                await sceneWorkflow.loadScript(selectedChapterId.value)
                if (sceneWorkflow.script.value) {
                    await transitionWorkflow.loadTransitions(sceneWorkflow.script.value.id)
                }
            } catch (error) {
                // Script doesn't exist yet, that's OK - user will create it
                console.log('No script found for this chapter yet')
            }

            determineCurrentStep()
        } catch (error) {
            console.error('Failed to load data:', error)
        } finally {
            loading.value = false
        }
    }

    const goBack = () => {
        if (projectId.value) {
            router.push({ name: 'ProjectDetail', params: { projectId: projectId.value } })
        } else {
            router.push('/projects')
        }
    }

    // Watch for chapter changes
    watch(selectedChapterId, (newId) => {
        if (newId) {
            loadData()
        }
    })

    // Watch for route changes
    watch(() => route.params, (newParams) => {
        console.log('Route params changed:', newParams)
        if (newParams.projectId) {
            projectId.value = newParams.projectId
        }
        if (newParams.chapterId) {
            selectedChapterId.value = newParams.chapterId
        }
    }, { deep: true })

    onMounted(() => {
        if (selectedChapterId.value && projectId.value) {
            loadData()
        }
    })

    return {
        // State
        selectedChapterId,
        projectId,
        currentStep,
        loading,

        // Workflows
        characterWorkflow,
        sceneWorkflow,
        shotWorkflow,
        transitionWorkflow,

        // Computed
        canExtractScenes,
        canExtractShots,
        canGenerateKeyframes,
        canCreateTransitions,
        canGenerateTransitionVideos,

        // Methods
        loadData,
        goBack
    }
}
