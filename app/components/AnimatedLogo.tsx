'use client'

import { useEffect, useState } from 'react'

const FRAMES = [
  `
   ▄████▄   ▄▄▄       ▄▄▄▄    ▄▄▄       ██▓    
  ▒██▀ ▀█  ▒████▄    ▓█████▄  ▒████▄    ▓██▒    
  ▒▓█    ▄ ▒██  ▀█▄  ▒██▒ ▄██ ▒██  ▀█▄  ▒██░    
  ▒▓▓▄ ▄██▒░██▄▄▄▄██ ▒██░█▀   ░██▄▄▄▄██ ▒██░    
  ▒ ▓███▀ ░ ▓█   ▓██▒░▓█  ▀█▓  ▓█   ▓██▒░██████▒
  ░ ░▒ ▒  ░ ▒▒   ▓▒█░░▒▓███▀▒  ▒▒   ▓▒█░░ ▒░▓  ░
    ░  ▒     ▒   ▒▒ ░▒░▒   ░    ▒   ▒▒ ░░ ░ ▒  ░
  ░          ░   ▒    ░    ░    ░   ▒     ░ ░   
  ░ ░            ░  ░ ░              ░  ░    ░  ░
  ░                        ░                      
  `,
  `
   ▄████▄   ▄▄▄       ▄▄▄▄    ▄▄▄       ██▓    
  ▒██▀ ▀█  ▒████▄    ▓█████▄  ▒████▄    ▓██▒    
  ▒▓█    ▄ ▒██  ▀█▄  ▒██▒ ▄██ ▒██  ▀█▄  ▒██░    
  ▒▓▓▄ ▄██▒░██▄▄▄▄██ ▒██░█▀   ░██▄▄▄▄██ ▒██░    
  ▒ ▓███▀ ░ ▓█   ▓██▒░▓█  ▀█▓  ▓█   ▓██▒░██████▒
  ░ ░▒ ▒  ░ ▒▒   ▓▒█░░▒▓███▀▒  ▒▒   ▓▒█░░ ▒░▓  ░
    ░  ▒     ▒   ▒▒ ░▒░▒   ░    ▒   ▒▒ ░░ ░ ▒  ░
  ░          ░   ▒    ░    ░    ░   ▒     ░ ░   
  ░ ░            ░  ░ ░              ░  ░    ░  ░
  ░                        ░                      
  `
]

export const AnimatedLogo = () => {
  const [frame, setFrame] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setFrame((prev) => (prev + 1) % FRAMES.length)
    }, 500)

    return () => clearInterval(interval)
  }, [])

  return (
    <pre className="hidden text-xs text-purple-400 transition-opacity duration-300 lg:block">
      {FRAMES[frame]}
    </pre>
  )
} 