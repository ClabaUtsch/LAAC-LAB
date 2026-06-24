<?php

namespace App\Http\Requests\Plan;

use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Foundation\Http\FormRequest;

class PlanRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return false;
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
             'name'             => 'required|string|max:255',
        'description'      => 'nullable|string',
        'price'            => 'required|numeric|min:0',
        'max_users'        => 'integer|min:1',
        'storage_limit_mb' => 'integer|min:1',
        'active'           => 'boolean',
        ];
    }
}
