"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTrigger, DialogTitle } from "@/components/ui/dialog"
import { ConfigPanel } from "@/components/config"
import { Settings, Database } from "@/lib/icons"

interface NavbarProps {
  config: {
    supabaseUrl: string
    supabaseKey: string
    openaiKey: string
  }
  onConfigSave: (config: {
    supabaseUrl: string
    supabaseKey: string
    openaiKey: string
  }) => void
}

export function Navbar({ config, onConfigSave }: NavbarProps) {
  const [isConfigOpen, setIsConfigOpen] = useState(false)

  const handleConfigSave = (newConfig: typeof config) => {
    onConfigSave(newConfig)
    setIsConfigOpen(false)
  }

  return (
    <motion.nav 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="border-b bg-card/80 backdrop-blur-sm flex-shrink-0 sticky top-0 z-50"
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <motion.div
            className="flex items-center gap-3"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <motion.div
              className="w-8 h-8 supabase-gradient rounded-lg flex items-center justify-center"
              whileHover={{ scale: 1.1, rotate: 360 }}
              transition={{ duration: 0.3 }}
            >
              <Database className="w-5 h-5 text-white" />
            </motion.div>
            <div className="flex flex-col">
              <h1 className="text-lg font-bold text-foreground">
                Supabase AI Assistant
              </h1>
              <p className="text-xs text-muted-foreground">
                Query your database with natural language
              </p>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <Dialog open={isConfigOpen} onOpenChange={setIsConfigOpen}>
              <DialogTrigger asChild>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button 
                    variant="ghost" 
                    size="icon"
                    className="h-9 w-9 hover:bg-muted"
                  >
                    <Settings className="w-4 h-4" />
                    <span className="sr-only">Open configuration</span>
                  </Button>
                </motion.div>
              </DialogTrigger>
              <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
                <DialogTitle className="sr-only">Configuration Settings</DialogTitle>
                <ConfigPanel 
                  onConfigSave={handleConfigSave} 
                  initialConfig={config}
                />
              </DialogContent>
            </Dialog>
          </motion.div>
        </div>
      </div>
    </motion.nav>
  )
}
