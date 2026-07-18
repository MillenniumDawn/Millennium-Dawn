Includes = {
}

PixelShader =
{
	Samplers =
	{
		TextureOne =
		{
			Index = 0
			MagFilter = "Point"
			MinFilter = "Point"
			MipFilter = "None"
			AddressU = "Wrap"
			AddressV = "Wrap"
		}
		TextureTwo =
		{
			Index = 1
			MagFilter = "Point"
			MinFilter = "Point"
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
		
		VS_OUTPUT main(const VS_INPUT v )
		{
			VS_OUTPUT Out;
		   	Out.vPosition  = mul( WorldViewProjectionMatrix, v.vPosition );
			Out.vTexCoord0  = v.vTexCoord;

			return Out;
		}
		
	]]
}

PixelShader =
{
    MainCode PixelColor
    [[
        
        float4 main( VS_OUTPUT v ) : PDX_COLOR
        {
            float2 uv = v.vTexCoord0 - 0.5f;
            float dist = length(uv);
            float outerRadius = 0.5f;
            float innerRadius = 0.3f;
            float aaWidth = 0.01f;

            // Maska pierścienia z AA (zamiast discard)
            float maskOuter = smoothstep(outerRadius, outerRadius - aaWidth, dist);
            float maskInner = smoothstep(innerRadius, innerRadius + aaWidth, dist);
            float ringMask = maskOuter * maskInner;

            if (ringMask <= 0.0f) discard;

            // Kąt (0 = góra, rośnie zgodnie z ruchem wskazówek)
            float angle = atan2(uv.y, -uv.x) - 1.5707963268f;
            if (angle < 0.0f) angle += 6.283185307f;

            float progress = CurrentState * 6.283185307f;

            float4 col;
            if (angle < progress)
            {
                col = vFirstColor;
            }
            else
            {
                col = vSecondColor;
            }

            col.a *= ringMask;
            return col;
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
	PixelShader = "PixelTexture"
}

