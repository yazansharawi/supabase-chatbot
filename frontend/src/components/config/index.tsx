"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Eye, EyeOff, Settings, Save, Shield} from "@/lib/icons"
import { ConfigPanelProps } from "./config.interface"

export function ConfigPanel({ onConfigSave, initialConfig }: ConfigPanelProps) {
  const [config, setConfig] = useState({
    supabaseUrl: initialConfig?.supabaseUrl || "",
    supabaseKey: initialConfig?.supabaseKey || "",
    openaiKey: initialConfig?.openaiKey || ""
  })

  const [showKeys, setShowKeys] = useState({
    supabaseKey: false,
    openaiKey: false
  })

  const [errors, setErrors] = useState<string[]>([])

  const validateConfig = () => {
    const newErrors: string[] = []

    if (!config.supabaseUrl.trim()) {
      newErrors.push("Supabase URL is required")
    } else if (!config.supabaseUrl.startsWith("https://")) {
      newErrors.push("Supabase URL must start with https://")
    }

    if (!config.supabaseKey.trim()) {
      newErrors.push("Supabase API Key is required")
    }

    if (!config.openaiKey.trim()) {
      newErrors.push("OpenAI API Key is required")
    } else if (!config.openaiKey.startsWith("sk-")) {
      newErrors.push("OpenAI API Key must start with sk-")
    }

    setErrors(newErrors)
    return newErrors.length === 0
  }

  const handleSave = () => {
    if (validateConfig()) {
      onConfigSave(config)
    }
  }

  const toggleKeyVisibility = (key: 'supabaseKey' | 'openaiKey') => {
    setShowKeys(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-4"
    >
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <motion.div 
            className="w-8 h-8 supabase-gradient rounded-lg flex items-center justify-center"
            whileHover={{ scale: 1.1, rotate: 180 }}
            transition={{ duration: 0.3 }}
          >
            <Settings className="w-5 h-5 text-white" />
          </motion.div>
          <h2 className="text-xl font-bold text-foreground">Configuration</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Configure your Supabase and OpenAI credentials to start chatting with your database
        </p>
      </div>

      <div className="space-y-4">
          <AnimatePresence>
            {errors.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Alert variant="destructive">
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1">
                      {errors.map((error, index) => (
                        <motion.li 
                          key={index}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          {error}
                        </motion.li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div 
            className="space-y-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            <label htmlFor="supabase-url" className="text-sm font-semibold text-foreground">
              Supabase URL
            </label>
            <motion.div
              whileFocus={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <Input
                id="supabase-url"
                placeholder="https://your-project.supabase.co"
                value={config.supabaseUrl}
                onChange={(e) => setConfig(prev => ({ ...prev, supabaseUrl: e.target.value }))}
                className="h-9 text-sm"
              />
            </motion.div>
            <p className="text-sm text-muted-foreground">
              Your Supabase project URL from the project settings
            </p>
          </motion.div>

          <motion.div 
            className="space-y-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <label htmlFor="supabase-key" className="text-sm font-semibold text-foreground">
              Supabase Anon Key
            </label>
            <motion.div 
              className="relative"
              whileFocus={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <Input
                id="supabase-key"
                type={showKeys.supabaseKey ? "text" : "password"}
                placeholder="eyJhbGciOiJIUzR5cCI6IkpXVCJ9..."
                value={config.supabaseKey}
                onChange={(e) => setConfig(prev => ({ ...prev, supabaseKey: e.target.value }))}
                className="pr-12 h-9 text-sm"
              />
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => toggleKeyVisibility('supabaseKey')}
                >
                  {showKeys.supabaseKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              </motion.div>
            </motion.div>
            <p className="text-sm text-muted-foreground">
              Your Supabase anonymous key from the project API settings
            </p>
          </motion.div>

          <motion.div 
            className="space-y-2"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            <label htmlFor="openai-key" className="text-sm font-semibold text-foreground">
              OpenAI API Key
            </label>
            <motion.div 
              className="relative"
              whileFocus={{ scale: 1.02 }}
              transition={{ duration: 0.2 }}
            >
              <Input
                id="openai-key"
                type={showKeys.openaiKey ? "text" : "password"}
                placeholder="sk-..."
                value={config.openaiKey}
                onChange={(e) => setConfig(prev => ({ ...prev, openaiKey: e.target.value }))}
                className="pr-12 h-9 text-sm"
              />
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => toggleKeyVisibility('openaiKey')}
                >
                  {showKeys.openaiKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </Button>
              </motion.div>
            </motion.div>
            <p className="text-sm text-muted-foreground">
              Your OpenAI API key for natural language processing
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Button 
              onClick={handleSave} 
              className="w-full h-9 text-sm font-semibold mt-4"
              size="lg"
              disabled={!config.supabaseUrl || !config.supabaseKey || !config.openaiKey}
            >
              <Save className="w-4 h-4 mr-2" />
              Save Configuration
            </Button>
          </motion.div>

        <motion.div 
          className="text-sm text-muted-foreground space-y-2 pt-4 border-t border-border"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <p className="flex items-start gap-2">
            <Shield className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
            <span><strong>Security:</strong> Your credentials are stored locally in your browser and are not sent to any external services except for the configured APIs.</span>
          </p>
        </motion.div>
      </div>
    </motion.div>
  )
} 