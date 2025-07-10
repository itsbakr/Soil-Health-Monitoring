import { createMiddlewareClient } from '@supabase/auth-helpers-nextjs'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(req: NextRequest) {
  const res = NextResponse.next()
  const supabase = createMiddlewareClient({ req, res })

  // Refresh session if expired - required for Server Components
  const {
    data: { session },
  } = await supabase.auth.getSession()

  // Define protected routes
  const protectedPaths = ['/dashboard', '/farms']
  const authPaths = ['/auth/login', '/auth/register']
  const currentPath = req.nextUrl.pathname

  // Check if current path is protected
  const isProtectedPath = protectedPaths.some(path => 
    currentPath.startsWith(path)
  )

  // Check if current path is auth page
  const isAuthPath = authPaths.some(path => 
    currentPath.startsWith(path)
  )

  // If user is trying to access protected route without session
  if (isProtectedPath && !session) {
    // Redirect to login with return URL
    const redirectUrl = new URL('/auth/login', req.url)
    redirectUrl.searchParams.set('redirectTo', currentPath)
    return NextResponse.redirect(redirectUrl)
  }

  // If user is logged in and trying to access auth pages
  if (isAuthPath && session) {
    // Check if there's a redirect URL
    const redirectTo = req.nextUrl.searchParams.get('redirectTo')
    if (redirectTo) {
      return NextResponse.redirect(new URL(redirectTo, req.url))
    }
    // Otherwise redirect to dashboard
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  return res
}

// Specify which routes this middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public folder)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
} 