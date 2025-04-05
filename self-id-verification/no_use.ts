// middleware.ts
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  // 1) Skip /api/verify entirely.
  //    If it's exactly "/api/verify" or starts with that path, let it continue.
  const { pathname } = request.nextUrl;
  console.log("Middleware path:", pathname);
  if (pathname.startsWith('/api/verify')) {
    return NextResponse.next();
  }

  // 2) Check the "verifiedUserId" cookie
  const verifiedUserId = request.nextUrl.searchParams.get('userId');
  // (In older Next.js, you'd do `request.cookies.verifiedUserId`, or parse them manually.)

  if (!verifiedUserId) {
    // If there's no verifiedUserId, block or redirect.
    // Here we simply return 401.
    return new NextResponse('Unauthorized (User not verified)', { status: 401 });
  }

  // 3) If verified, rewrite to the external domain 
  //    (a reverse-proxy). For example:
  //
  //    https://<your_ngrok>.ngrok-free.app/<whatever path>?<same query>
  //
  // Note: NextResponse.rewrite() can handle external URLs 
  // in Next.js 12.2+ with the "experimental" external rewrite feature 
  // or Next.js 13. 
  const externalUrl = new URL(`https://1eea-2001-b011-3813-111f-3d7d-4343-e8c4-d91.ngrok-free.app${pathname}`);
  externalUrl.search = request.nextUrl.search; // preserve query params

  return NextResponse.rewrite(externalUrl);
}

export const config = {
  matcher: ['/api/:path*'], // ✅ 只針對 API 生效
};