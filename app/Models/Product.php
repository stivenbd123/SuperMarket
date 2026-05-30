<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    protected $fillable = ['category_id', 'sku', 'name', 'description', 'price',
    'stock', 'min_stock', 'unit', 'image_url',
    ];
     protected $casts = [
        'price' => 'decimal:2',
        'stock' => 'integer',
        'min_stock' => 'integer',
    ];

    public function category(){
        return $this->belongsTo(category::class);
    }

    public function orders(){
        return $this->hasMany(Order::class);
    }

    public function inventoryLogs(){
        return $this->hasMany(InventoryLog::class);
    }
}
