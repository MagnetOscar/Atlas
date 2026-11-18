<script setup lang="ts">
import type { GlobeInstance } from 'globe.gl'
import type { Material, MeshPhongMaterial, ShaderMaterial, Texture } from 'three'
import type { NodeData } from '@/stores/nodes'
import {
  useDocumentVisibility,
  useElementSize,
  useElementVisibility,
} from '@vueuse/core'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useNodeGeoClusters } from '@/composables/useNodeGeoClusters'
import { useAppStore } from '@/stores/app'
import { buildEarthArcs } from '@/utils/earthArcs'

const props = defineProps<{
  nodes?: NodeData[]
}>()

const EARTH_DAY_TEXTURE = '/images/earth/earth-blue-marble.jpg'
const EARTH_NIGHT_TEXTURE = '/images/earth/earth-night.jpg'
const EARTH_BUMP_MAP = '/images/earth/earth-topology.png'
const EARTH_SPECULAR_MAP = '/images/earth/earth-water.png'
const CHINA_COORD: [number, number] = [35.8617, 104.1954]
const MAX_FLAG_BOXES = 64
const FLAG_CLEARANCE_PX = 5
const DEFAULT_FLAG_SIZE_PX = 19.2

const appStore = useAppStore()

const containerRef = ref<HTMLDivElement>()
const globeHostRef = ref<HTMLDivElement>()
const { width: containerWidth, height: containerHeight } = useElementSize(containerRef)

const documentVisibility = useDocumentVisibility()
const elementVisible = useElementVisibility(containerRef)
const shouldRender = computed(() => documentVisibility.value === 'visible' && elementVisible.value)

let globe: GlobeInstance | null = null
let globeMaterial: MeshPhongMaterial | null = null
let waterSpecularMap: Texture | null = null
let loadingGlobe = false
let destroyed = false

interface GlobePoint {
  id: string
  lat: number
  lng: number
  code: string
  servers: number
  onlineServers: number
}

interface GlobeLabel {
  id: string
  lat: number
  lng: number
  code: string
}

interface GlobeArc {
  id: string
  startLat: number
  startLng: number
  endLat: number
  endLng: number
}

const {
  displayNodes,
  regionClusters,
  locationByNodeUuid,
  totalServers,
  onlineServers,
  offlineServers,
  clusterKey,
} = useNodeGeoClusters({ nodes: () => props.nodes })

const earthArcs = computed(() => buildEarthArcs(
  appStore.earthArcMode,
  regionClusters.value,
  displayNodes.value,
  locationByNodeUuid.value,
))
const persistentEarthArcs = computed(() => appStore.earthArcMode === 'persistent')

const arcsData = computed<GlobeArc[]>(() => earthArcs.value.map(arc => ({
  id: arc.id,
  startLat: arc.from[0],
  startLng: arc.from[1],
  endLat: arc.to[0],
  endLng: arc.to[1],
})))

const pointsData = computed<GlobePoint[]>(() => regionClusters.value.map(cluster => ({
  id: cluster.id,
  lat: cluster.coord[0],
  lng: cluster.coord[1],
  code: cluster.code,
  servers: cluster.servers,
  onlineServers: cluster.onlineServers,
})))

const labelsData = computed<GlobeLabel[]>(() => regionClusters.value.map(cluster => ({
  id: cluster.id,
  lat: cluster.coord[0],
  lng: cluster.coord[1],
  code: cluster.code,
})))

function earthTextureUrl() {
  return appStore.isDark ? EARTH_NIGHT_TEXTURE : EARTH_DAY_TEXTURE
}

function pointColor(point: object): string {
  const data = point as GlobePoint
  if (data.onlineServers > 0)
    return appStore.isDark ? 'rgba(34, 211, 238, 1)' : 'rgba(2, 132, 199, 0.98)'
  return appStore.isDark ? 'rgba(250, 204, 21, 0.92)' : 'rgba(202, 138, 4, 0.88)'
}

function createLabelElement(data: object): HTMLElement {
  const label = data as GlobeLabel
  const root = document.createElement('div')
  root.className = 'earth-label'
  root.dataset.clusterId = label.id

  const flag = document.createElement('img')
  flag.className = 'earth-label-flag'
  flag.src = `/images/flags/${label.code}.svg`
  flag.alt = label.code
  root.appendChild(flag)

  return root
}

function getRenderSize() {
  const width = containerWidth.value || globeHostRef.value?.clientWidth || 320
  const height = containerHeight.value || globeHostRef.value?.clientHeight || width
  return { width, height }
}

function resizeGlobe() {
  if (!globe)
    return
  const { width, height } = getRenderSize()
  globe.width(width).height(height)
}

function resetPointOfView(transitionMs = 0) {
  globe?.pointOfView({ lat: CHINA_COORD[0], lng: CHINA_COORD[1], altitude: 1.95 }, transitionMs)
}

function applyControls() {
  if (!globe)
    return
  const controls = globe.controls()
  controls.autoRotate = shouldRender.value && !appStore.stopEarth
  controls.autoRotateSpeed = 1.6
  controls.enableDamping = true
  controls.enableZoom = false
  controls.enablePan = false
  controls.rotateSpeed = 0.55
}

function applyMaterialStyle() {
  if (!globe || !globeMaterial)
    return
  globe.globeImageUrl(earthTextureUrl())
  globeMaterial.bumpScale = appStore.isDark ? 0.02 : 0.03
  globeMaterial.shininess = appStore.isDark ? 8 : 14
  globeMaterial.emissive.set(appStore.isDark ? 0x1E3A5F : 0x355C7D)
  globeMaterial.emissiveIntensity = appStore.isDark ? 0.48 : 0.32
  globeMaterial.needsUpdate = true
  globe
    .pointColor(pointColor)
    .arcColor(() => appStore.isDark ? 'rgba(56, 189, 248, 0.82)' : 'rgba(2, 132, 199, 0.72)')
    .ringColor(() => appStore.isDark ? 'rgba(45, 212, 191, 0.34)' : 'rgba(14, 165, 233, 0.28)')
    .atmosphereColor(appStore.isDark ? '#38bdf8' : '#60a5fa')
    .atmosphereAltitude(appStore.isDark ? 0.14 : 0.11)
}

function syncDataToGlobe() {
  if (!globe)
    return
  globe
    .pointsData(pointsData.value)
    .ringsData(pointsData.value)
    .arcsData(arcsData.value)
    .htmlElementsData(labelsData.value)
  applyArcStyle()
}

function applyArcStyle() {
  if (!globe)
    return
  globe
    .arcDashLength(persistentEarthArcs.value ? 1 : 0.06)
    .arcDashGap(persistentEarthArcs.value ? 0 : 0.03)
    .arcDashAnimateTime(persistentEarthArcs.value ? 0 : 1800)
}

interface GlobeSceneObject {
  __globeObjType?: string
  element?: HTMLElement
  children?: Array<{ material?: Material }>
}

function patchArcMaterialForFlagAvoidance(
  material: Material | undefined,
  sharedUniforms: {
    uFlagCount: { value: number }
    uFlagBoxes: { value: unknown[] }
    uFlagRadius: { value: number }
  },
) {
  const shaderMat = material as ShaderMaterial | undefined
  if (!shaderMat || !shaderMat.fragmentShader || shaderMat.userData.__atlasFlagAvoidancePatched)
    return
  if (!shaderMat.fragmentShader.includes('gl_FragColor'))
    return

  shaderMat.userData.__atlasFlagAvoidancePatched = true
  shaderMat.uniforms.uFlagCount = sharedUniforms.uFlagCount
  shaderMat.uniforms.uFlagBoxes = sharedUniforms.uFlagBoxes
  shaderMat.uniforms.uFlagRadius = sharedUniforms.uFlagRadius
  shaderMat.fragmentShader = shaderMat.fragmentShader
    .replace(
      'void main() {',
      `uniform int uFlagCount;\nuniform vec4 uFlagBoxes[${MAX_FLAG_BOXES}];\nuniform float uFlagRadius;\nvoid main() {\n  for (int i = 0; i < ${MAX_FLAG_BOXES}; i++) {\n    if (i >= uFlagCount) break;\n    vec4 box = uFlagBoxes[i];\n    vec2 d = abs(gl_FragCoord.xy - box.xy) - box.zw;\n    float dist = length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - uFlagRadius;\n    if (dist < 0.0) discard;\n  }`,
    )
  shaderMat.needsUpdate = true
}

async function startGlobe() {
  if (globe || loadingGlobe || !globeHostRef.value)
    return

  loadingGlobe = true
  await nextTick()

  try {
    const [{ default: Globe }, THREE] = await Promise.all([
      import('globe.gl'),
      import('three'),
    ])

    if (destroyed || !globeHostRef.value)
      return

    const { width, height } = getRenderSize()
    globe = new Globe(globeHostRef.value, {
      rendererConfig: { alpha: true, antialias: true },
    })
      .width(width)
      .height(height)
      .backgroundColor('rgba(0,0,0,0)')
      .globeImageUrl(earthTextureUrl())
      .bumpImageUrl(EARTH_BUMP_MAP)
      .showAtmosphere(true)
      .pointsData(pointsData.value)
      .pointLat('lat')
      .pointLng('lng')
      .pointAltitude(0.008)
      .pointRadius((point: object) => ((point as GlobePoint).onlineServers > 0 ? 0.22 : 0.13))
      .pointColor(pointColor)
      .pointsMerge(false)
      .pointsTransitionDuration(500)
      .ringsData(pointsData.value)
      .ringLat('lat')
      .ringLng('lng')
      .ringColor(() => appStore.isDark ? 'rgba(45, 212, 191, 0.34)' : 'rgba(14, 165, 233, 0.28)')
      .ringMaxRadius(1.4)
      .ringPropagationSpeed(0.8)
      .ringRepeatPeriod(2400)
      .arcsData(arcsData.value)
      .arcStartLat('startLat')
      .arcStartLng('startLng')
      .arcEndLat('endLat')
      .arcEndLng('endLng')
      .arcColor(() => appStore.isDark ? 'rgba(56, 189, 248, 0.82)' : 'rgba(2, 132, 199, 0.72)')
      .arcAltitudeAutoScale(0.42)
      .arcStroke(0.45)
      .arcDashLength(persistentEarthArcs.value ? 1 : 0.06)
      .arcDashGap(persistentEarthArcs.value ? 0 : 0.03)
      .arcDashAnimateTime(persistentEarthArcs.value ? 0 : 1800)
      .arcsTransitionDuration(500)
      .htmlElementsData(labelsData.value)
      .htmlLat('lat')
      .htmlLng('lng')
      .htmlAltitude(0.012)
      .htmlElement(createLabelElement)
      .htmlElementVisibilityModifier((el: HTMLElement, isVisible: boolean) => {
        const wasVisible = el.dataset.globeVisible === '1'
        el.dataset.globeVisible = isVisible ? '1' : '0'
        if (isVisible)
          delete el.dataset.globeHideUntil
        else if (wasVisible)
          el.dataset.globeHideUntil = String(performance.now() + 450)
        el.style.opacity = isVisible ? '1' : '0'
        el.style.filter = isVisible ? 'blur(0)' : 'blur(14px)'
      })
      .htmlTransitionDuration(500)

    const drawSize = new THREE.Vector2()
    const projVec = new THREE.Vector3()
    const flagBoxes: InstanceType<typeof THREE.Vector4>[] = []
    for (let i = 0; i < MAX_FLAG_BOXES; i++)
      flagBoxes.push(new THREE.Vector4())
    const sharedFlagUniforms = {
      uFlagCount: { value: 0 },
      uFlagBoxes: { value: flagBoxes },
      uFlagRadius: { value: 4 },
    }
    const scene = globe.scene()
    scene.onBeforeRender = (renderer, currentScene, camera) => {
      renderer.getDrawingBufferSize(drawSize)
      const clientW = renderer.domElement.clientWidth || drawSize.x
      const clientH = renderer.domElement.clientHeight || drawSize.y
      const scaleX = drawSize.x / clientW
      const scaleY = drawSize.y / clientH
      sharedFlagUniforms.uFlagRadius.value = 3.5 * scaleX

      const now = performance.now()
      let flagCount = 0
      currentScene.traverse((node) => {
        const sceneObj = node as unknown as GlobeSceneObject & { getWorldPosition?: (target: typeof projVec) => typeof projVec }
        if (sceneObj.__globeObjType === 'html') {
          const el = sceneObj.element
          const hideUntil = Number(el?.dataset.globeHideUntil || '0')
          if (!el || (el.dataset.globeVisible !== '1' && now > hideUntil) || flagCount >= MAX_FLAG_BOXES || !sceneObj.getWorldPosition)
            return
          sceneObj.getWorldPosition(projVec).project(camera)
          if (projVec.z < -1 || projVec.z > 1)
            return
          const flagImg = el.firstElementChild as HTMLElement | null
          const cssW = flagImg?.offsetWidth || DEFAULT_FLAG_SIZE_PX
          const cssH = flagImg?.offsetHeight || DEFAULT_FLAG_SIZE_PX
          const cx = (projVec.x * 0.5 + 0.5) * drawSize.x
          const cy = (projVec.y * 0.5 + 0.5) * drawSize.y
          const halfW = (cssW * 0.5 + FLAG_CLEARANCE_PX - 3.5) * scaleX
          const halfH = (cssH * 0.5 + FLAG_CLEARANCE_PX - 3.5) * scaleY
          sharedFlagUniforms.uFlagBoxes.value[flagCount]!.set(cx, cy, Math.max(1, halfW), Math.max(1, halfH))
          flagCount++
          return
        }
        if (sceneObj.__globeObjType === 'arc' && sceneObj.children?.length) {
          patchArcMaterialForFlagAvoidance(sceneObj.children[0]?.material, sharedFlagUniforms)
        }
      })
      sharedFlagUniforms.uFlagCount.value = flagCount
    }

    const renderer = globe.renderer()
    renderer.setClearColor(0x000000, 0)
    renderer.domElement.style.background = 'transparent'

    const material = globe.globeMaterial()
    if ('shininess' in material) {
      globeMaterial = material as MeshPhongMaterial
      waterSpecularMap = new THREE.TextureLoader().load(EARTH_SPECULAR_MAP, () => {
        if (!globeMaterial)
          return
        globeMaterial.specularMap = waterSpecularMap
        globeMaterial.needsUpdate = true
      })
      globeMaterial.specular = new THREE.Color(appStore.isDark ? 0x64748B : 0x475569)
    }

    const frontLight = new THREE.DirectionalLight(0xFFFFFF, appStore.isDark ? 0.9 : 1.0)
    frontLight.position.set(1.2, 1.1, 1.6)
    const leftFill = new THREE.DirectionalLight(0xDBEAFE, appStore.isDark ? 0.62 : 0.48)
    leftFill.position.set(-1.2, 0.2, 1.2)
    const rearFill = new THREE.DirectionalLight(0xE0F2FE, appStore.isDark ? 0.52 : 0.38)
    rearFill.position.set(-1.0, -0.8, -1.2)
    globe.lights([
      new THREE.AmbientLight(0xFFFFFF, appStore.isDark ? 1.85 : 1.45),
      frontLight,
      leftFill,
      rearFill,
    ])

    applyMaterialStyle()
    applyControls()
    resetPointOfView(0)
    if (!shouldRender.value)
      globe.pauseAnimation()
  }
  finally {
    loadingGlobe = false
  }
}

function stopGlobe() {
  if (!globe)
    return

  globe.scene().onBeforeRender = () => {}
  globe.pauseAnimation()
  globe._destructor()
  globe = null
  globeMaterial = null
  waterSpecularMap?.dispose()
  waterSpecularMap = null
  if (globeHostRef.value)
    globeHostRef.value.replaceChildren()
}

onMounted(() => {
  void startGlobe()
})

onBeforeUnmount(() => {
  destroyed = true
  stopGlobe()
})

watch([containerWidth, containerHeight], ([width, height]) => {
  if (width <= 0 || height <= 0)
    return
  resizeGlobe()
})

watch([
  () => regionClusters.value.map(clusterKey).join(','),
  () => earthArcs.value.map(arc => `${arc.id}:${arc.from.join(',')}:${arc.to.join(',')}`).join('|'),
  () => appStore.earthArcMode,
], () => {
  syncDataToGlobe()
})

watch(() => appStore.isDark, () => {
  applyMaterialStyle()
})

watch(() => appStore.stopEarth, (stopped) => {
  applyControls()
  if (stopped)
    resetPointOfView(300)
})

watch(shouldRender, (visible) => {
  if (!globe)
    return
  if (visible) {
    globe.resumeAnimation()
    applyControls()
    resizeGlobe()
    return
  }
  globe.pauseAnimation()
  applyControls()
})
</script>

<template>
  <div ref="containerRef" :data-earth-arc-count="earthArcs.length" :data-earth-arc-motion="persistentEarthArcs ? 'persistent' : 'dynamic'" class="relative z-0 aspect-square w-full max-w-md mx-auto translate-y-2 md:-translate-y-1 overflow-visible pointer-events-none">
    <div ref="globeHostRef" class="earth-globe-host absolute inset-0 z-0 w-full h-full scale-106 select-none touch-auto pointer-events-auto cursor-grab active:cursor-grabbing" />

    <div
      v-if="totalServers > 0"
      class="absolute top-6 md:top-12 left-0 text-[10px] text-muted-foreground pointer-events-none flex gap-2 items-center backdrop-blur-lg bg-background/60 rounded px-2 py-0.5"
    >
      <div v-if="onlineServers > 0" class="flex items-center gap-1">
        <span class="inline-block size-1.5 rounded-full bg-green-600 animate-pulse" />
        <span class="text-green-600">{{ onlineServers }}</span>
      </div>
      <div v-if="offlineServers > 0" class="flex items-center gap-1">
        <span class="inline-block size-1.5 rounded-full bg-yellow-600 animate-pulse" />
        <span class="text-yellow-600">{{ offlineServers }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.earth-globe-host {
  contain: layout paint;
  background: transparent;
}

.earth-globe-host :deep(canvas) {
  background: transparent !important;
  outline: none;
}

.earth-globe-host :deep(.scene-container) {
  background: transparent !important;
}

.earth-globe-host :deep(.earth-label) {
  pointer-events: none;
  position: relative;
  transform: translate(-50%, -118%);
  transition:
    opacity 500ms ease,
    filter 500ms ease;
  will-change: opacity, filter;
}

.earth-globe-host :deep(.earth-label-flag) {
  position: relative;
  z-index: 2;
  width: 1.2rem;
  height: 1.2rem;
  display: block;
  border-radius: 0.18rem;
  box-shadow: 0 8px 20px rgb(15 23 42 / 24%);
}
</style>
