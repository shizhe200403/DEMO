import { onBeforeUnmount, ref, watch, type ComputedRef, type Ref } from "vue";

type NumberSource = Ref<number> | ComputedRef<number>;

export function useAnimatedNumber(
  source: NumberSource,
  options?: {
    duration?: number;
    decimals?: number;
  },
) {
  const duration = options?.duration ?? 480;
  const decimals = options?.decimals ?? 0;
  const animated = ref(Number(source.value || 0));
  let frame = 0;

  const stopAnimation = () => {
    if (frame) {
      cancelAnimationFrame(frame);
      frame = 0;
    }
  };

  const commitValue = (value: number) => {
    const factor = 10 ** decimals;
    animated.value = Math.round(value * factor) / factor;
  };

  watch(
    source,
    (nextValue) => {
      stopAnimation();

      const startValue = Number(animated.value || 0);
      const targetValue = Number(nextValue || 0);
      if (!Number.isFinite(targetValue)) {
        commitValue(0);
        return;
      }

      if (Math.abs(targetValue - startValue) < 0.001) {
        commitValue(targetValue);
        return;
      }

      const start = performance.now();

      const tick = (now: number) => {
        const progress = Math.min(1, (now - start) / duration);
        const eased = 1 - (1 - progress) ** 3;
        commitValue(startValue + (targetValue - startValue) * eased);
        if (progress < 1) {
          frame = requestAnimationFrame(tick);
          return;
        }
        frame = 0;
      };

      frame = requestAnimationFrame(tick);
    },
    { immediate: true },
  );

  onBeforeUnmount(() => {
    stopAnimation();
  });

  return animated;
}
