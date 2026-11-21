import { useEffect } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'

gsap.registerPlugin(ScrollTrigger)

export const prefersReduced = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * Landing-page motion: Lenis is the only smooth-scroll engine, driven by GSAP's ticker
 * and feeding ScrollTrigger. Under reduced motion nothing is initialised and every
 * element is already in its final state.
 */
export function useLandingMotion(rootRef) {
  useEffect(() => {
    const root = rootRef.current
    if (!root || prefersReduced()) return

    const lenis = new Lenis({ duration: 1.05, smoothWheel: true })
    const raf = (t) => lenis.raf(t * 1000)
    lenis.on('scroll', ScrollTrigger.update)
    gsap.ticker.add(raf)
    gsap.ticker.lagSmoothing(0)
    window.__lenis = lenis

    const ctx = gsap.context(() => {
      // hero intro: words, then supporting copy; nav and CTA are usable throughout
      gsap.from('.hero [data-split] .wi', { yPercent: 105, duration: 0.9, ease: 'power3.out', stagger: 0.045, delay: 0.1 })
      gsap.from('.hero [data-hero-fade]', { y: 14, opacity: 0, duration: 0.7, ease: 'power2.out', stagger: 0.08, delay: 0.45 })
      gsap.from('.hero .trace', { y: 24, opacity: 0, duration: 0.9, ease: 'power2.out', delay: 0.25 })

      gsap.utils.toArray('section:not(.hero) [data-split]').forEach((el) => {
        gsap.from(el.querySelectorAll('.wi'), {
          yPercent: 105, duration: 0.8, ease: 'power3.out', stagger: 0.035,
          scrollTrigger: { trigger: el, start: 'top 85%', once: true },
        })
      })
      gsap.utils.toArray('[data-reveal]').forEach((el) => {
        gsap.from(el, { y: 22, opacity: 0, duration: 0.8, ease: 'power2.out', scrollTrigger: { trigger: el, start: 'top 88%', once: true } })
      })
    }, root)

    const refresh = () => ScrollTrigger.refresh()
    document.fonts?.ready.then(refresh)
    window.addEventListener('load', refresh)

    return () => {
      window.removeEventListener('load', refresh)
      ctx.revert()
      gsap.ticker.remove(raf)
      lenis.destroy()
      delete window.__lenis
    }
  }, [rootRef])
}
