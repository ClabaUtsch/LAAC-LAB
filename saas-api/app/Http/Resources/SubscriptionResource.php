<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class SubscriptionResource extends JsonResource
{
    // app/Http/Resources/SubscriptionResource.php
    public function toArray($request): array
    {
        return [
            'id'         => $this->id,
            'status'     => $this->status,
            'plan'       => new PlanResource($this->whenLoaded('plan')),
            'starts_at'  => $this->starts_at?->format('d/m/Y'),
            'ends_at'    => $this->ends_at?->format('d/m/Y'),
        ];
    }
}

