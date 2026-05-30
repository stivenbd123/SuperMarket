<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Product;

class ProductController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {
        $query = Product::query();
        
        if($request->has('category_id') && $request->category_id != ''){
            $query->where('category_id', $request->category_id);
        }

        if($request->has('id') && $request->id != ''){
            $query->where('id', $request->id);
        }

        

        return response()->json($query->orderBy('created_at', 'desc')->get(), 200);

        
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $request->validate([
            'name' => 'required|string|max:40',
            'sku' => 'unique|string|max:50',
            'description' => 'nullable|string|max:70',
            'price' => 'required|decimal',
            'stock'  => 'required|integer',
            'min_stock' => 'required|integer',
            'unit' => 'required|string|in:unidad,libra,kilo,litro',
            'photo' => 'required|image|mimes:jpeg,png,webp|max:2048'
        ]);

        $product_photo = $request->file('photo')->store('product_photos', 'public');

        $product = Product::create([

            'name' => $request->name,
            'sku' 

        ])

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
    public function update(Request $request, string $id)
    {
        //
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(string $id)
    {
        //
    }
}
