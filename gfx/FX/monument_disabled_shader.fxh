VertexStruct VS_INPUT
{
	float3 vPosition  : POSITION;
	float2 vTexCoord  : TEXCOORD0;
};

ConstantBuffer( 0, 0 )
{
	float4x4 WorldViewProjectionMatrix;
	float4 Color;
	float2 Offset;
	float2 NextOffset;
	float Time;
	float AnimationTime;
};
PixelShader =
{
	Code
	[[
	float4 desaturateRGB(float4 col, float dF)
	{
		float3 blend = float3(dF, dF, dF);
		float gray = (col.r + col.g + col.b)/3.0;
		float3 gray3 = float3(gray, gray, gray);
		//
		float4 outCol = float4(lerp(col.rgb, gray, blend), col.a);
		return outCol;
	}
	]]
};