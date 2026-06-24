<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class CheckRole
{
    /**
     * Handle an incoming request.
     *
     * @param  Closure(Request): (Response)  $next
     */
    public function handle(Request $request, Closure $next, string ...$roles): mixed
    {
        if(!in_array($request->user()->role, $roles)){
            return response()->json([
                'message' => 'No tienes permiso para esta accion'
            ], 403);
        }
        return $next($request);
    }
}
