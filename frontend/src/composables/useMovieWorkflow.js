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
    const projectId = ref(route.query.projectId || null)
    const currentStep = ref(0)
    const loading = ref(false)

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

    // Load all data
    const loadData = async () => {
        if (!selectedChapterId.value) return

        loading.value = true
        try {
            await Promise.all([
                characterWorkflow.loadCharacters(),
                sceneWorkflow.loadScript(selectedChapterId.value)
            ])

            if (sceneWorkflow.script.value) {
                await transitionWorkflow.loadTransitions(sceneWorkflow.script.value.id)
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
            if (route.params.chapterId !== newId) {
                router.push({ name: 'MovieStudio', params: { chapterId: newId } })
            }
            loadData()
        }
    })

    onMounted(() => {
        if (selectedChapterId.value) {
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
