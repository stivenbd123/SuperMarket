<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\ProductController;



//Ruoutes protected by sanctum 

Route::middleware('auth:sanctum')->group(function(){
    Route::get('/products', [ProductController::class, 'index']);      

    
    Route::get('/user', function (Request $request) {
        return $request->user();
        })->middleware('auth:sanctum');


    Route::post('/products', [ProductController::class, 'store']);       


});
