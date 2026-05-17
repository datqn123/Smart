import { useState, useEffect, useCallback, useRef } from "react"
import { synthesizeSpeech } from "../api/aiChatSse"

export function stripMarkdownForSpeech(text: string): string {
  return text
    .replace(/\*\*/g, "")
    .replace(/#{1,6}\s/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[*_~]/g, "")
}

interface UseTextToSpeechReturn {
  speak: (text: string) => Promise<void>
  stop: () => void
  pause: () => void
  resume: () => void
  isSpeaking: boolean
  isPaused: boolean
  isLoading: boolean
  supported: boolean
}

export function useTextToSpeech(): UseTextToSpeechReturn {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const urlRef = useRef<string | null>(null)
  const speakGenRef = useRef(0)

  const revokeUrl = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current)
      urlRef.current = null
    }
  }, [])

  const stop = useCallback(() => {
    speakGenRef.current += 1
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      audioRef.current = null
    }
    revokeUrl()
    setIsSpeaking(false)
    setIsPaused(false)
    setIsLoading(false)
  }, [revokeUrl])

  useEffect(() => () => stop(), [stop])

  const speak = useCallback(
    async (text: string) => {
      const cleanText = stripMarkdownForSpeech(text).trim()
      if (!cleanText) return

      stop()
      const gen = speakGenRef.current + 1
      speakGenRef.current = gen
      setIsLoading(true)

      try {
        const blob = await synthesizeSpeech(cleanText)
        if (speakGenRef.current !== gen) return

        revokeUrl()
        const url = URL.createObjectURL(blob)
        urlRef.current = url
        const audio = new Audio(url)
        audioRef.current = audio

        audio.onended = () => {
          if (speakGenRef.current !== gen) return
          setIsSpeaking(false)
          setIsPaused(false)
          revokeUrl()
        }
        audio.onerror = () => {
          if (speakGenRef.current !== gen) return
          setIsSpeaking(false)
          setIsPaused(false)
          revokeUrl()
        }

        await audio.play()
        if (speakGenRef.current !== gen) return
        setIsSpeaking(true)
        setIsPaused(false)
      } catch {
        if (speakGenRef.current === gen) {
          setIsSpeaking(false)
          setIsPaused(false)
        }
      } finally {
        if (speakGenRef.current === gen) {
          setIsLoading(false)
        }
      }
    },
    [stop, revokeUrl]
  )

  const pause = useCallback(() => {
    audioRef.current?.pause()
    setIsPaused(true)
  }, [])

  const resume = useCallback(() => {
    void audioRef.current?.play()
    setIsPaused(false)
  }, [])

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    isLoading,
    supported: true,
  }
}
