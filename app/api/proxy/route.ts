import { NextResponse } from 'next/server';

export const runtime = 'edge';

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const targetUrl = url.searchParams.get('url');

  if (!targetUrl) {
    return NextResponse.json(
      { error: 'No URL provided' }, 
      { 
        status: 400,
        headers: corsHeaders()
      }
    );
  }

  try {
    const response = await fetch(targetUrl, {
      headers: {
        'Accept': 'application/json'
      }
    });

    const data = await response.json();
    return NextResponse.json(data, { headers: corsHeaders() });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch data' },
      { 
        status: 500,
        headers: corsHeaders()
      }
    );
  }
} 