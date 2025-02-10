import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'

const execAsync = promisify(exec)

export async function GET() {
  try {
    const scriptPath = path.join(process.cwd(), 'scripts/funding_analysis.py')
    const { stdout, stderr } = await execAsync(`python ${scriptPath}`)

    if (stderr) {
      console.error('Script error:', stderr)
      return NextResponse.json({ error: stderr }, { status: 500 })
    }

    const data = JSON.parse(stdout)
    return NextResponse.json(data)
  } catch (error) {
    console.error('Funding analysis error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to analyze funding data' },
      { status: 500 }
    )
  }
} 