<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\User;
use App\Models\Product;
use App\Models\InventoryLog;
use Illuminate\Support\Facades\DB;

class InventoryLogController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {
        $query = InventoryLog::with('product:id,name', 'user:id,name');
        //entrada, salida, ajuste, venta
        if($request->has('type')&& $request->type != ''){
            $query->where('type', $request->type); 
        }

        if($request->has('from') &&  $request->has('to')){
            $query->whereBetween('created_at', [$request->from, $request->to]);
        }

        return response()->json([
            'data' => $query->orderBy('created_at', 'desc')->paginate(10) 
        ]);

    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $request->validate([
            'movements' => 'required|array|min:1',
            'movements.*.product_id' => 'required|exists:products,id',
            'movements.*.type' => 'required|in:entrada,salida,venta,ajuste',
            'movements.*.motive' => 'required|string|max:400',
            'movements.*.quantity' => 'required|integer|min:1'
        ]);

        $logs = [];

    DB::transaction(function () use ($request, &$logs){
        foreach ($request->movements as $movement) {
            $product = Product::findOrFail($movement['product_id']);
            $stock_before = $product->stock;
            
            if ($movement['type'] === 'entrada') {
                $product->stock += $movement['quantity'];
            }
            else{
                if($product->stock < $movement['quantity']){
                    throw new \Exception("Error stock actual del producto {$product->name} es {$product->stock}");
                }
                $product->stock -= $movement['quantity'];
            }
            $product->save();

            $logs[] = InventoryLog::create([
                'product_id' => $product->id,     
                'user_id' => $request->user()->id,   
                'type' => $movement['type'],
                'motive' => $movement['motive'],
                'quantity' => $movement['quantity'],
                'stock_before' => $stock_before,
                'stock_after' =>  $product->stock 
            ]);
        }

        
    });
    return response()->json([
        'message' => count($logs) . 'movimientos registrados. ',
        'data' => $logs
    ], 201);
    }

    /**
     * Display the specified resource.
     */
    public function show($id)
    {
        $inventory = InventoryLog::with('user', 'product')->find($id);

        if (!$inventory) {
            return response()->json([
                'message' => 'No hay registros encontrados'
            ], 404);
        }

        return response()->json($inventory);

    }

    public function byProduct(Request $request, Product $product){
        $inventory_log = InventoryLog::where('product_id', $product->id)
        ->with('user:id,name')->orderBy('created_at', 'desc')
        ->paginate($request->get('per_page', 10));
        
        return response()->json([
            'Producto' => $product->name,
            'stock' => $product->stock,
            'data' => $inventory_log
        ]);
        }
}
