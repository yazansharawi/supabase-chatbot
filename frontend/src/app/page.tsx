"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChatInterface } from "@/components/chat"
import { ConfigPanel } from "@/components/config"
import { Navbar } from "@/components/ui/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Database, Sparkles } from "@/lib/icons"

export default function Home() {
  const [config, setConfig] = useState({
    supabaseUrl: "",
    supabaseKey: "",
    openaiKey: ""
  })

  const [isConfigured, setIsConfigured] = useState(false)
  const [canSkipConfig, setCanSkipConfig] = useState(false)
  const [isLoading, setIsLoading] = useState(true)


  useEffect(() => {
    const checkExistingConfig = async () => {
      try {
        const response = await fetch('/api/config')
        if (response.ok) {
          const data = await response.json()
          if (data.canSkipConfig) {
            setConfig({
              supabaseUrl: data.supabaseUrl,
              supabaseKey: "", 
              openaiKey: ""    
            })
            setCanSkipConfig(true)
          }
        }
      } catch (error) {
        console.error('Error checking existing config:', error)
      } finally {
        setIsLoading(false)
      }
    }

    checkExistingConfig()
  }, [])

  const handleConfigSave = (newConfig: typeof config) => {
    setConfig(newConfig)
    setIsConfigured(true)
    setCanSkipConfig(false)
  }

  const handleSkipConfig = () => {
    setIsConfigured(true)
  }

  return (
    <main className="min-h-screen bg-background">
      {isConfigured ? (
        <>
          <Navbar config={config} onConfigSave={handleConfigSave} />
          <div className="container mx-auto p-4 h-[calc(100vh-4rem)] flex flex-col overflow-hidden">
            <ChatInterface config={config} />
          </div>
        </>
      ) : (
        <div className="h-screen flex flex-col supabase-hero-bg overflow-hidden">
          <motion.nav
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="border-b bg-card/80 backdrop-blur-sm flex-shrink-0"
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
              </div>
            </div>
          </motion.nav>

          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 flex items-center justify-center"
              >
                <div className="text-center">
                  <motion.div
                    className="rounded-full h-12 w-12 border-4 border-primary/20 border-t-primary mx-auto mb-4"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  />
                  <motion.p
                    className="text-muted-foreground"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    Checking configuration...
                  </motion.p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="content"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6 }}
                className="flex-1 flex items-center justify-center px-4 py-4 overflow-y-auto"
              >
                <div className="w-full max-w-6xl">
                  <motion.div
                    className="space-y-6"
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8, duration: 0.6 }}
                  >
                    {canSkipConfig ? (
                      <div className="grid lg:grid-cols-2 gap-6 items-start">
                        <motion.div
                          initial={{ opacity: 0, x: 50 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 1.0, duration: 0.6 }}
                          className="order-2 lg:order-1"
                        >
                          <Card className="border-2 border-primary/30 bg-primary/10 shadow-lg h-fit">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-lg text-center text-primary flex items-center justify-center gap-2">
                                <motion.div
                                  animate={{ rotate: [0, 360] }}
                                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                >
                                  <Sparkles className="w-4 h-4" />
                                </motion.div>
                                Configuration Found!
                              </CardTitle>
                              <CardDescription className="text-center text-sm">
                                You can use your existing settings or update them.
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="pt-0">
                              <motion.div
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                              >
                                <Button
                                  onClick={handleSkipConfig}
                                  className="w-full mb-3 h-10 text-sm font-semibold"
                                  size="lg"
                                >
                                  Continue with Existing Configuration
                                </Button>
                              </motion.div>
                              <p className="text-xs text-center text-muted-foreground">
                                or configure new settings
                              </p>
                            </CardContent>
                          </Card>
                        </motion.div>

                        <motion.div
                          initial={{ opacity: 0, x: -50 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.8, duration: 0.6 }}
                          className="order-1 lg:order-2"
                        >
                          <ConfigPanel onConfigSave={handleConfigSave} />
                        </motion.div>
                      </div>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8, duration: 0.6 }}
                        className="max-w-lg mx-auto"
                      >
                        <ConfigPanel onConfigSave={handleConfigSave} />
                      </motion.div>
                    )}
                  </motion.div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </main>
  )
}
