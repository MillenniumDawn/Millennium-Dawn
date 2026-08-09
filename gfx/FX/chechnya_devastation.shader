Includes = {
}

PixelShader =
{
    Samplers =
    {
        TextureOne =
        {
            Index = 0
            MagFilter = "Linear"
            MinFilter = "Linear"
            MipFilter = "None"
            AddressU = "Wrap"
            AddressV = "Wrap"
        }
        TextureTwo =
        {
            Index = 1
            MagFilter = "Linear"
            MinFilter = "Linear"
            MipFilter = "None"
            AddressU = "Wrap"
            AddressV = "Wrap"
        }
    }
}


VertexStruct VS_INPUT
{
    float4 vPosition  : POSITION;
    float2 vTexCoord  : TEXCOORD0;
};

VertexStruct VS_OUTPUT
{
    float4  vPosition : PDX_POSITION;
    float2  vTexCoord0 : TEXCOORD0;
};


ConstantBuffer( 0, 0 )
{
    float4x4 WorldViewProjectionMatrix;
    float4 vFirstColor;   
    float4 vSecondColor;  
    float CurrentState;   
};


VertexShader =
{
    MainCode VertexShader
    [[
        VS_OUTPUT main(const VS_INPUT v)
        {
            VS_OUTPUT Out;
            Out.vPosition  = mul(WorldViewProjectionMatrix, v.vPosition);
            Out.vTexCoord0 = v.vTexCoord;
            return Out;
        }
    ]]
}

PixelShader =
{
    MainCode PixelColor
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR
        {
            float2 uv = v.vTexCoord0;

            // ── 1. Aspect Ratio Normalization ───────────────────────────
            float aspect = 14.0f; 
            float2 aspectUV = float2(uv.x * aspect, uv.y);

            // ── 2. Dark Hard Thin Border Frame ──────────────────────────
            float borderY = 0.035f; 
            float borderX = borderY / aspect;

            bool isBorder = (uv.x < borderX || uv.x > (1.0f - borderX) ||
                             uv.y < borderY || uv.y > (1.0f - borderY));

            if (isBorder)
            {
                // Dark matte graphite frame
                return float4(0.07f, 0.08f, 0.10f, 1.0f);
            }

            // Remap UV coordinates inside inner track
            float2 innerUV;
            innerUV.x = (uv.x - borderX) / (1.0f - 2.0f * borderX);
            innerUV.y = (uv.y - borderY) / (1.0f - 2.0f * borderY);

            // ── 3. Blurred Fill Boundary ─────────────────────────────────
            // Instead of a hard cutoff, blend smoothly across a small band
            // straddling CurrentState so the red fades into black.
            float blurWidth = 0.004f; // widen/narrow this to taste
            float fillBlend = saturate((CurrentState + blurWidth - innerUV.x) / (2.0f * blurWidth));
            fillBlend = smoothstep(0.0f, 1.0f, fillBlend); // ease the transition

            // ── 4. Unfilled Section (Near Black Trough) ─────────────────
            float3 unlitBg = float3(0.012f, 0.014f, 0.018f);

            // Laser light spill into unlit section from progress edge
            float distFromFill = innerUV.x - CurrentState;
            if (distFromFill > 0.0f && distFromFill < 0.05f)
            {
                float lightSpill = exp(-distFromFill * 35.0f);
                unlitBg += float3(0.45f, 0.05f, 0.04f) * lightSpill * 0.25f;
            }
            unlitBg = clamp(unlitBg, 0.0f, 1.0f);

            // ── 5. Red Volumetric Base Color ────────────────────────────
            float4 darkRed   = float4(0.32f, 0.02f, 0.03f, 1.0f); 
            float4 brightRed = float4(0.62f, 0.08f, 0.06f, 1.0f); 

            float gradT = clamp(innerUV.x / (CurrentState + 0.001f), 0.0f, 1.0f);
            float4 baseRed = lerp(darkRed, brightRed, gradT);

            // ── 6. Pattern: Directional Tactical Chevrons (`>>>`) ───────
            float chevronDensity = 1.2f;
            float chevronShape = abs(innerUV.y - 0.5f) * 1.5f + aspectUV.x;
            float chevronPattern = frac(chevronShape * chevronDensity);
            float chevronMask = smoothstep(.4, 0.0f, chevronPattern) - smoothstep(0.85f, 0.95f, chevronPattern);

            // Apply subtle shading to alternate chevrons
            float3 patternRed = lerp(baseRed.rgb, baseRed.rgb * 1.28f, chevronMask * 0.25f);

            // ── 7. Glass Glare & CRT Volumetric Lighting ────────────────
            float centerCurve = sin(innerUV.y * 3.14159f);
            float glassHighlight = pow(centerCurve, 3.0f) * 0.30f;
            
            // Clean CRT top glass glare line
            float topGlass = smoothstep(0.06f, 0.20f, innerUV.y) * smoothstep(0.38f, 0.20f, innerUV.y) * 0.22f;

            // Combine lighting layers
            patternRed = patternRed * (0.70f + 0.50f * centerCurve) + float3(glassHighlight, glassHighlight, glassHighlight);
            patternRed += float3(0.6f, 0.7f, 0.85f) * topGlass;

            // ── 8. Smooth Hot Leading Edge ──────────────────────────────
            float edgeDist = CurrentState - innerUV.x;
            if (edgeDist < 0.025f && edgeDist > -blurWidth)
            {
                float edgeGlow = saturate(1.0f - (edgeDist / 0.025f));
                patternRed += float3(0.30f, 0.12f, 0.08f) * pow(edgeGlow, 1.8f);
            }
            patternRed = clamp(patternRed, 0.0f, 1.0f);

            // ── 9. Final Blend Between Trough and Red Fill ───────────────
            float3 finalColor = lerp(unlitBg, patternRed, fillBlend);

            return float4(clamp(finalColor, 0.0f, 1.0f), 1.0f);
        }
    ]]

    MainCode PixelTexture
    [[
        float4 main(VS_OUTPUT v) : PDX_COLOR
        {
            return float4(1, 1, 1, 1);
        }
    ]]
}


BlendState BlendState
{
    BlendEnable = yes
    SourceBlend = "SRC_ALPHA"
    DestBlend = "INV_SRC_ALPHA"
}


Effect Color
{
    VertexShader = "VertexShader"
    PixelShader = "PixelColor"
}

Effect Texture
{
    VertexShader = "VertexShader"
    PixelShader = "PixelColor"
}