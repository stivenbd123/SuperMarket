<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\User;
use App\Models\Order;
Use App\Models\Product;
Use App\Models\InventoryLog;
use Illuminate\Support\Facades\DB;

class OrderController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {
        $order = Order::with('user', 'products');

        if($request->has('user_id') && $request->user_id != ''){
            $order->where('user_id', $request->user_id);
        }

        if($request->has('status')){
            $order->where('status', $request->status);
        }

        if($request->has('from') && $request->has('to')){
            $order->whereBetween('created_at', [$request->from, $request->to]);
        }

        return response()->json($order->get());
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
    $user = $request->user();

    $request->validate([
        'products' => 'required|array|min:1',
        'products.*.product_id' => 'required|exists:products,id',
        'products.*.quantity' => 'required|integer|min:1' 

    ]);

    $order = DB::transaction(function () use ($request, $user){

        $order = Order::create([
            'user_id' => $user->id,
            'total' => 0,
            'status' => 'completada'
        ]);

        $total = 0;

        foreach($request->products as $item){
            $product = Product::FindOrfail($item['product_id']);

            if($product->stock < $item['quantity']){
                throw new \Exception(
                    "Stock insuficiente del producto: $product->name, stock disponible $product->stock"
                );
            }

            $sub_total = $product->price * $item['quantity'];
            $total += $sub_total;

            $order->products()->attach($product->id, [
                'quantity' => $item['quantity'],
                'unit_price' => $product->price,
                'subtotal' => $sub_total
            ]);

            $stock_before = $product->stock;            
            $product->decrement('stock', $item['quantity']);

            InventoryLog::create([
                'product_id' => $product->id,
                'user_id' => $user->id,
                'type' => 'venta',
                'motive' => "venta #$order->id",
                'quantity' => $item['quantity'],
                'stock_before' => $stock_before,
                'stock_after' => $product->stock
            ]); 

            
            
            }
            $order->update(['total' => $total]);

            return $order;
    });
    
    return response()->json([
        'message' => 'Orden creada con exito',
        'order' => $order->load('products')
    ], 201);

    }

    /**
     * Display the specified resource.
     */
    public function show($id)
    {
        $order = Order::with(['user', 'products'])->find($id);

        if(!$order){
            return response()->json([
                'message' => 'Orden no encontrada'
            ], 404);
        }

        return response()->json($order);
    }

    /**
     * Update the specified resource in storage.
     */
    public function cancel(Request $request, $id)
    {
        $order = Order::with('products')->find($id);

        if(!$order){
            return response()->json([
                'message' => 'Orden no encontrada'
            ], 404);
        }

        if($order->status === 'cancelada'){
            return response()->json([
                'message' => 'Esta orden ya ha sido cancelada'
            ]);
        }

        if ($order->created_at->diffInHours(now()) >= 24) {
            return response()->json([
                'message' => 'No se puede cancelar, han pasado más de 24 horas'
            ], 400);
        }

        DB::transaction(function() use ($order, $request){
            foreach ($order->products as $product) {
                $stock_before = $product->stock;
                $quantity = $product->pivot->quantity;

                $product->increment('stock', $quantity);

                    InventoryLog::create([
                    'product_id' => $product->id,
                    'user_id' => $request->user()->id,
                    'type' => 'ajuste',
                    'motive' => "cancelacion venta #" . $order->id,
                    'quantity' => $quantity,
                    'stock_before' => $stock_before,
                    'stock_after' => $product->stock
                ]);

                }
            $order->update(['status' => 'cancelada']);
        });
            return response()->json([
            'message' => 'orden cancelada, stock devuelto',
            'orden' => $order->fresh('products')
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
