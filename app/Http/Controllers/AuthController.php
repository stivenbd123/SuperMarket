<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash; 
use App\Models\User;

class AuthController extends Controller
{
    public function register(Request $request){

        $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => 'required|string|min:4|confirmed'
        ]);

        $user = User::create([
            'name' => $request->name, 
            'email' => $request->email,
            'password' => Hash::make($request->password),
            'role' => 'cajero'
        ]);

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'message' => 'Usuario registrado con exito',
            'token' => $token
        ], 200);
    }

    public function login(Request $request){

        $request->validate([
            'email' => 'required|email',
            'password' => 'required'
        ]); 

        if(!Auth::attempt($request->only('email', 'password'))){
            return response()->json([
                'message' => 'credenciales incorrectas'
            ], 401);
        }

        $user = $request->user();
        $token = $user->createToken('auth_token')->plainTextToken;
        
        return response()->json([
            'user' => $user,
            'token' => $token 
        ], 200);
    }

    public function logout(Request $request){

        $request->user()->currentAccessToken()->delete();
        
        return response()->json([
            'message' => 'Sesion cerrada correctamente'
        ], 200);
    }
}
