<?php

namespace App\Http\Controllers;
use App\Models\Category;
use App\Models\Product;

use Illuminate\Http\Request;

class CategoryController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {   
        $categories = Category::select('id', 'name')->get();

        return response()->json($categories);

    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {

        $request->validate([
            'name' => 'required|string|max:50',
            'description' => 'required|string|max:200'
        ]);

        $category = Category::create([
            'name' => $request->name,
            'description' => $request->description
        ]);

        return response()->json([
            'Success' => $category
        ], 200);
        
    }

    /**
     * Display the specified resource.
     */
    public function show(string $id)
    {
        //
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, $id)
    {
        $category = Category::find($id);

        if(!$category){
            return response()->json([
                'message' => 'Categoria no encontrada'
            ], 404); 
        }

        $request->validate([
            'name' => 'sometimes|string|max:50',
            'description' => 'sometimes|string|max:50'
        ]);

        $category->update($request->validated());

        return response()->json([
            'message' => 'Categoria actualizada correctamente',
            'update' => $category
        ], 200);

    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(string $id)
    {
        //
    }
}
