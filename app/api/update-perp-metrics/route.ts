import { NextResponse } from 'next/server';
import { updatePerpMetrics } from '@/app/workers/perp-metrics-worker';

export async function POST() {
  try {
    const data = await updatePerpMetrics();
    return NextResponse.json({ success: true, data });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to update metrics' },
      { status: 500 }
    );
  }
} 