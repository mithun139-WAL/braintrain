import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function proxy(request: NextRequest) {
    const token = request.cookies.get('token')?.value; // Adjust to match your expected auth cookie Name

    const isAuthPage = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/register');
    const isDashboardPage = request.nextUrl.pathname.startsWith('/sessions') || request.nextUrl.pathname.startsWith('/analytics');

    if (!token && isDashboardPage) {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    if (token && isAuthPage) {
        return NextResponse.redirect(new URL('/', request.url)) // redirect to dashboard/home
    }

    return NextResponse.next()
}

export const config = {
    matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
