export interface Config {
  supabaseUrl: string
  supabaseKey: string
  openaiKey: string
}

export interface ConfigPanelProps {
  onConfigSave: (config: Config) => void
  initialConfig?: Config
}