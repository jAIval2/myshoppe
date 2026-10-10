import { randomUUID } from "node:crypto";
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const nonce = Buffer.from(randomUUID()).toString("base64");
  const development = process.env.NODE_ENV === "development";
  const supabaseOrigin = process.env.SUPABASE_URL
    ? new URL(process.env.SUPABASE_URL).origin
    : "";
  const policy = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' https://checkout.razorpay.com${development ? " 'unsafe-eval'" : ""}`,
    `style-src 'self' 'nonce-${nonce}'`,
    "style-src-attr 'unsafe-inline'",
    `img-src 'self' data: blob: https://images.unsplash.com https://images.pexels.com${supabaseOrigin ? ` ${supabaseOrigin}` : ""}`,
    "font-src 'self' data:",
    `media-src 'self' blob:${supabaseOrigin ? ` ${supabaseOrigin}` : ""}`,
    `connect-src 'self' https://api.razorpay.com https://checkout.razorpay.com${supabaseOrigin ? ` ${supabaseOrigin}` : ""}`,
    "frame-src 'self' https://api.razorpay.com https://checkout.razorpay.com",
    "form-action 'self' https://api.razorpay.com",
    "base-uri 'self'",
    "object-src 'none'",
    "frame-ancestors 'none'",
  ].join("; ");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", policy);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", policy);
  return response;
}

export const config = {
  matcher: ["/((?!api|uploads|media|fonts|_next/static|_next/image|favicon.ico|icon.svg|.*\\..*).*)"],
};
