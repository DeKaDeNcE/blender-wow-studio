// Library code

vec2 posToTexCoord(vec3 cameraPoint, vec3 normal){
     //    vec3 normPos = -normalize(cameraPoint.xyz);
     //    vec3 normPos = cameraPoint.xyz;
     //    vec3 reflection = reflect(normPos, normal);
     //    return (normalize(vec3(reflection.r, reflection.g, reflection.b + 1.0)).rg * 0.5) + vec2(0.5);

     vec3 normPos_495 = normalize(cameraPoint.xyz);
     vec3 temp_500 = (normPos_495 - (normal * (2.0 * dot(normPos_495, normal))));
     vec3 temp_657 = vec3(temp_500.x, temp_500.y, (temp_500.z + 1.0));

     return ((normalize(temp_657).xy * 0.5) + vec2(0.5));
 }

 float edgeScan(vec3 position, vec3 normal){
     float dotProductClamped = clamp(dot(-normalize(position),normal), 0.000000, 1.000000);
     return clamp(2.700000 * dotProductClamped * dotProductClamped - 0.400000, 0.000000, 1.000000);
 }

 mat3 blizzTranspose(mat4 value) {
     return mat3(
     value[0].xyz,
     value[1].xyz,
     value[2].xyz
     );
 }

// Shader code
#ifdef COMPILING_VS

precision highp float;

/* vertex shader code */
in vec3 aPosition;
in vec3 aNormal;
in vec2 aTexCoord;
in vec2 aTexCoord2;


// Whole model
uniform mat4 uViewProjectionMatrix;
uniform mat4 uPlacementMatrix;

//Individual meshes
uniform vec4 color_Transparency;

//Shader output
out vec3 vPosition;
out vec3 vNormal;
out vec2 vTexCoord;
out vec2 vTexCoord2;
out vec2 vTexCoord3;
out vec4 vDiffuseColor;


void main() {

    vec4 aPositionVec4 = vec4(aPosition, 1.0f);

    vec4 lDiffuseColor = color_Transparency;
    vec4 combinedColor = clamp(lDiffuseColor /*+ vc_matEmissive*/, 0.000000, 1.000000);
    vec4 combinedColorHalved = combinedColor * 0.5;

    mat3 viewModelMatTransposed = mat3(uViewProjectionMatrix);
    mat4 cameraMatrix = uViewProjectionMatrix;
    vec4 cameraPoint = cameraMatrix * (uPlacementMatrix * aPositionVec4);

    // Handle normals
    vec3 normal = normalize(viewModelMatTransposed * (mat3(uPlacementMatrix) * aNormal));

    vec2 envCoord = posToTexCoord(cameraPoint.xyz, normal);
    float edgeScanVal = edgeScan(cameraPoint.xyz, normal);

    // Handle colors and texture coordinates
    vTexCoord2 = vec2(0.0);
    vTexCoord3 = vec2(0.0);

    //Diffuse_T1
    #if VERTEXSHADER == 0
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
    #endif
    //Diffuse_Env
    #if VERTEXSHADER == 1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = envCoord;
    #endif
    //Diffuse_T1_T2
    #if VERTEXSHADER == 2
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord2;
    #endif
    #if VERTEXSHADER == 3 //Diffuse_T1_Env
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = envCoord;
    #endif
    #if VERTEXSHADER == 4 //Diffuse_Env_T1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = envCoord;
        vTexCoord2 = aTexCoord;
    #endif
    #if VERTEXSHADER == 5 //Diffuse_Env_Env
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = envCoord;
        vTexCoord2 = envCoord;
    #endif
    #if VERTEXSHADER == 6 //Diffuse_T1_Env_T1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = envCoord;
        vTexCoord3 = aTexCoord;
    #endif
    #if VERTEXSHADER == 7 //Diffuse_T1_T1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord;
    #endif
    #if VERTEXSHADER == 8 //Diffuse_T1_T1_T1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord;
        vTexCoord3 = aTexCoord;
    #endif
    #if VERTEXSHADER == 9 //Diffuse_EdgeFade_T1+
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a * edgeScanVal);
        vTexCoord = aTexCoord;
    #endif
    #if VERTEXSHADER == 10 //Diffuse_T2

        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord2;
    #endif
    #if VERTEXSHADER == 11 //Diffuse_T1_Env_T2
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = envCoord;
        vTexCoord3 = aTexCoord2;
    #endif
    #if VERTEXSHADER == 12 //Diffuse_EdgeFade_T1_T2
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a * edgeScanVal);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord2;
    #endif
    #if VERTEXSHADER == 13 //Diffuse_EdgeFade_Env
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a * edgeScanVal);
        vTexCoord = envCoord;
    #endif
    #if VERTEXSHADER == 14 //Diffuse_T1_T2_T1
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord2;
        vTexCoord3 = aTexCoord;
    #endif
    #if VERTEXSHADER == 15 //Diffuse_T1_T2_T3
        vDiffuseColor = vec4(combinedColorHalved.r, combinedColorHalved.g, combinedColorHalved.b, combinedColor.a);
        vTexCoord = aTexCoord;
        vTexCoord2 = aTexCoord2;
        vTexCoord3 = vTexCoord3;
    #endif
    #if VERTEXSHADER == 16 //Color_T1_T2_T3
        vec4 in_col0 = vec4(1.0, 1.0, 1.0, 1.0);
        vDiffuseColor = vec4((in_col0.rgb * 0.500000).r, (in_col0.rgb * 0.500000).g, (in_col0.rgb * 0.500000).b, in_col0.a);
        vTexCoord = aTexCoord2;
        vTexCoord2 = vec2(0.000000, 0.000000);
        vTexCoord3 = vTexCoord3;
    #endif
    #if VERTEXSHADER == 17 //BW_Diffuse_T1
        vDiffuseColor = vec4(combinedColor.rgb * 0.500000, combinedColor.a);
        vTexCoord = aTexCoord;
    #endif
    #if VERTEXSHADER == 18 //BW_Diffuse_T1_T2
        vDiffuseColor = vec4(combinedColor.rgb * 0.500000, combinedColor.a);
        vTexCoord = aTexCoord;
    #endif

    vNormal = normal;
    vPosition = cameraPoint.xyz;

    gl_Position = cameraPoint;

}

#endif //COMPILING_VS


#ifdef COMPILING_FS

precision highp float;

struct LocalLight
{
    vec4 color;
    vec4 position;
    vec4 attenuation;
};


in vec3 vNormal;
in vec2 vTexCoord;
in vec2 vTexCoord2;
in vec2 vTexCoord3;
in vec3 vPosition;
in vec4 vDiffuseColor;

uniform sampler2D uTexture;
uniform sampler2D uTexture2;
uniform sampler2D uTexture3;
uniform sampler2D uTexture4;


out vec4 outputColor;

//Whole model
uniform mat4 uViewProjectionMatrix;

uniform vec4 uSunDirAndFogStart;
uniform vec4 uSunColorAndFogEnd;
uniform vec4 uAmbientLight;



uniform ivec3 UnFogged_IsAffectedByLight_LightCount;
uniform vec4 uFogColorAndAlphaTest;
uniform LocalLight pc_lights[4];


vec3 makeDiffTerm(vec3 matDiffuse, vec3 accumLight) {
    vec3 currColor;
    float mult = 1.0;
    vec3 lDiffuse = vec3(0.0, 0.0, 0.0);
    vec4 viewUp = uViewProjectionMatrix * vec4(0, 0, 1, 0);

    if (UnFogged_IsAffectedByLight_LightCount.y == 1) {
        vec3 normalizedN = normalize(vNormal);
        float nDotL = clamp(dot(normalizedN, -(uSunDirAndFogStart.xyz)), 0.0, 1.0);
        float nDotUp = dot(normalizedN, viewUp.xyz);

        vec4 AmbientLight = uAmbientLight;

        vec3 adjAmbient = (AmbientLight.rgb );
        vec3 adjHorizAmbient = (AmbientLight.rgb );
        vec3 adjGroundAmbient = (AmbientLight.rgb );

        if ((nDotUp >= 0.0))
        {
            currColor = mix(adjHorizAmbient, adjAmbient, vec3(nDotUp));
        }
        else
        {
            currColor= mix(adjHorizAmbient, adjGroundAmbient, vec3(-(nDotUp)));
        }

        vec3 skyColor = (currColor * 1.10000002);
        vec3 groundColor = (currColor* 0.699999988);


        lDiffuse = (uSunColorAndFogEnd.xyz * nDotL);
        currColor = mix(groundColor, skyColor, vec3((0.5 + (0.5 * nDotL))));

    } else {
        currColor = vec3 (1.0, 1.0, 1.0) ;
        accumLight = vec3(0,0,0);
        mult = 1.0;
    }


    vec3 gammaDiffTerm = matDiffuse * (currColor + lDiffuse);
    vec3 linearDiffTerm = (matDiffuse * matDiffuse) * accumLight;

    return sqrt(gammaDiffTerm*gammaDiffTerm + linearDiffTerm) ;
}


void main() {

    /* Animation support */
    vec2 texCoord = vTexCoord.xy;
    vec2 texCoord2 = vTexCoord2.xy;
    vec2 texCoord3 = vTexCoord3.xy;

    vec3 gamma = vec3(0.454);

    /* Get color from texture */
    vec4 tex = texture(uTexture, texCoord).rgba;
    //tex = vec4(pow(tex.rgb, gamma), tex.a);

    vec4 tex2 = texture(uTexture2, texCoord2).rgba;
    //tex2 = vec4(pow(tex2.rgb, gamma), tex2.a);

    vec4 tex3 = texture(uTexture3, texCoord3).rgba;
    //tex3 = vec4(pow(tex3.rgb, gamma), tex3.a);


    vec4 tex2WithTextCoord1 = texture(uTexture2,texCoord);
    vec4 tex3WithTextCoord1 = texture(uTexture3,texCoord);
    vec4 tex4WithTextCoord2 = texture(uTexture4,texCoord2);

    vec4 finalColor = vec4(0);
    vec4 meshResColor = vDiffuseColor;

    vec3 accumLight;
    if ((UnFogged_IsAffectedByLight_LightCount.y == 1))
    {
        vec3 vPos3 = vPosition.xyz;
        vec3 vNormal3 = normalize(vNormal.xyz);
        vec3 lightColor = vec3(0.0);
        int count = int(pc_lights[0].attenuation.w);
        int index = 0;
        for (;;)
        {
            if ( index >= UnFogged_IsAffectedByLight_LightCount.z) break;
            LocalLight lightRecord = pc_lights[index];
            vec3 vectorToLight = ((lightRecord.position).xyz - vPos3);
            float distanceToLightSqr = dot(vectorToLight, vectorToLight);
            float distanceToLightInv = inversesqrt(distanceToLightSqr);
            float distanceToLight = (distanceToLightSqr * distanceToLightInv);
            float diffuseTerm1 = max((dot(vectorToLight, vNormal3) * distanceToLightInv), 0.0);
            vec4 attenuationRec = lightRecord.attenuation;

            float attenuation = (1.0 - clamp((distanceToLight - attenuationRec.x) * (1.0 / (attenuationRec.z - attenuationRec.x)), 0.0, 1.0));

            vec3 attenuatedColor = attenuation * lightRecord.color.xyz * attenuationRec.y;
            lightColor = (lightColor + vec3(attenuatedColor * attenuatedColor * diffuseTerm1 ));
            index++;
        }
        meshResColor.rgb = clamp(lightColor , 0.0, 1.0);
        accumLight = meshResColor.rgb;
        //finalColor.rgb =  finalColor.rgb * lightColor;
    }

    float opacity;
    float finalOpacity = 0.0;
    vec3 matDiffuse;
    vec3 specular = vec3(0.0, 0.0, 0.0);
    vec3 visParams = vec3(1.0, 1.0, 1.0);
    vec4 genericParams[3];
    genericParams[0] = vec4( 1.0, 1.0, 1.0, 1.0 );
    genericParams[1] = vec4( 1.0, 1.0, 1.0, 1.0 );
    genericParams[2] = vec4( 1.0, 1.0, 1.0, 1.0 );

    #if(FRAGMENTSHADER==0) //Combiners_Opaque
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==1) //Combiners_Mod
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = tex.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==2) //Combiners_Opaque_Mod
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb;
        opacity = tex2.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==3) //Combiners_Opaque_Mod2x
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb * 2.000000;
        opacity = tex2.a * 2.000000 * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==4) //Combiners_Opaque_Mod2xNA
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb * 2.000000;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==5) //Combiners_Opaque_Opaque
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==6) //Combiners_Mod_Mod
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb;
        opacity = tex.a * tex2.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==7) //Combiners_Mod_Mod2x
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb * 2.000000;
        opacity = tex.a * tex2.a * 2.000000 * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==8) //Combiners_Mod_Add
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = (tex.a + tex2.a) * vDiffuseColor.a;
        specular = tex2.rgb;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==9) //Combiners_Mod_Mod2xNA
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb * 2.000000;
        opacity = tex.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==10) //Combiners_Mod_AddNA
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = tex.a * vDiffuseColor.a;
        specular = tex2.rgb;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==11) //Combiners_Mod_Opaque
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * tex2.rgb;
        opacity = tex.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==12) //Combiners_Opaque_Mod2xNA_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * tex2.rgb * 2.000000, tex.rgb, vec3(tex.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==13) //Combiners_Opaque_AddAlpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        specular = tex2.rgb * tex2.a;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==14) //Combiners_Opaque_AddAlpha_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        specular = tex2.rgb * tex2.a * (1.000000 - tex.a);
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==15) //Combiners_Opaque_Mod2xNA_Alpha_Add
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * tex2.rgb * 2.000000, tex.rgb, vec3(tex.a));
        specular = tex3.rgb * tex3.a * genericParams[0].b;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==16) //Combiners_Mod_AddAlpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = tex.a * vDiffuseColor.a;
        specular = tex2.rgb * tex2.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==17) //Combiners_Mod_AddAlpha_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = (tex.a + tex2.a * (0.300000 * tex2.r + 0.590000 * tex2.g + 0.110000 * tex2.b)) * vDiffuseColor.a;
        specular = tex2.rgb * tex2.a * (1.000000 - tex.a);
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==18) //Combiners_Opaque_Alpha_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(mix(tex.rgb, tex2.rgb, vec3(tex2.a)), tex.rgb, vec3(tex.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==19) //Combiners_Opaque_Mod2xNA_Alpha_3s
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * tex2.rgb * 2.000000, tex3.rgb, vec3(tex3.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==20) //Combiners_Opaque_AddAlpha_Wgt
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        specular = tex2.rgb * tex2.a * genericParams[0].g;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==21) //Combiners_Mod_Add_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = (tex.a + tex2.a) * vDiffuseColor.a;
        specular = tex2.rgb * (1.000000 - tex.a);
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==22) //Combiners_Opaque_ModNA_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * tex2.rgb, tex.rgb, vec3(tex.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==23) //Combiners_Mod_AddAlpha_Wgt
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = tex.a * vDiffuseColor.a;
        specular = tex2.rgb * tex2.a * genericParams[0].g;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==24) //Combiners_Opaque_Mod_Add_Wgt
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb, tex2.rgb, vec3(tex2.a));
        specular = tex.rgb * tex.a * genericParams[0].r;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==25) //Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha
        float glowOpacity = clamp((tex3.a * genericParams[0].z), 0.0, 1.0);
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * tex2.rgb * 2.000000, tex.rgb, vec3(tex.a)) * (1.000000 - glowOpacity);
        specular = tex3.rgb * glowOpacity;
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==26) //Combiners_Mod_Dual_Crossfade
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(mix(tex, tex2WithTextCoord1, vec4(clamp(genericParams[0].g, 0.000000, 1.000000))), tex3WithTextCoord1, vec4(clamp(genericParams[0].b, 0.000000, 1.000000))).rgb;
        opacity = mix(mix(tex, tex2WithTextCoord1, vec4(clamp(genericParams[0].g, 0.000000, 1.000000))), tex3WithTextCoord1, vec4(clamp(genericParams[0].b, 0.000000, 1.000000))).a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==27) //Combiners_Opaque_Mod2xNA_Alpha_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(mix(tex.rgb * tex2.rgb * 2.000000, tex3.rgb, vec3(tex3.a)), tex.rgb, vec3(tex.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==28) //Combiners_Mod_Masked_Dual_Crossfade
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(mix(tex, tex2WithTextCoord1, vec4(clamp(genericParams[0].g, 0.000000, 1.000000))), tex3WithTextCoord1, vec4(clamp(genericParams[0].b, 0.000000, 1.000000))).rgb;
        opacity = mix(mix(tex, tex2WithTextCoord1, vec4(clamp(genericParams[0].g, 0.000000, 1.000000))), tex3WithTextCoord1, vec4(clamp(genericParams[0].b, 0.000000, 1.000000))).a * tex4WithTextCoord2.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==29) //Combiners_Opaque_Alpha
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb, tex2.rgb, vec3(tex2.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==30) //Guild
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * mix(genericParams[0].rgb, tex2.rgb * genericParams[1].rgb, vec3(tex2.a)), tex3.rgb * genericParams[2].rgb, vec3(tex3.a));
        opacity = tex.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==31) //Guild_NoBorder
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb * mix(genericParams[0].rgb, tex2.rgb * genericParams[1].rgb, vec3(tex2.a));
        opacity = tex.a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==32) //Guild_Opaque
        matDiffuse = vDiffuseColor.rgb * 2.000000 * mix(tex.rgb * mix(genericParams[0].rgb, tex2.rgb * genericParams[1].rgb, vec3(tex2.a)), tex3.rgb * genericParams[2].rgb, vec3(tex3.a));
        opacity = vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==33) //Combiners_Mod_Depth
        matDiffuse = vDiffuseColor.rgb * 2.000000 * tex.rgb;
        opacity = tex.a * vDiffuseColor.a * visParams.r;
        finalOpacity = opacity * visParams.r;
    #endif
    #if(FRAGMENTSHADER==34)  //Illum
        finalColor = vec4(1.0,1.0,1.0, 1.0);

        //Unusued
    #endif
    #if(FRAGMENTSHADER==35) //Combiners_Mod_Mod_Mod_Const
        matDiffuse = vDiffuseColor.rgb * 2.000000 * (tex * tex2 * tex3 * genericParams[0]).rgb;
        opacity = (tex * tex2 * tex3 * genericParams[0]).a * vDiffuseColor.a;
        finalOpacity = opacity * visParams.r;
    #endif

    finalColor = vec4(makeDiffTerm(matDiffuse, accumLight) + specular, finalOpacity);

    if(finalColor.a < uFogColorAndAlphaTest.w)
        discard;

    int uUnFogged = UnFogged_IsAffectedByLight_LightCount.x;
    float uFogEnd = uSunColorAndFogEnd.w;
    if (uUnFogged == 0) {

        vec3 fogColor = uFogColorAndAlphaTest.xyz;

        float fog_rate = 1.5;
        float fog_bias = 0.01;

        //vec4 fogHeightPlane = pc_fog.heightPlane;
        //float heightRate = pc_fog.color_and_heightRate.w;

        float distanceToCamera = length(vPosition.xyz);
        float z_depth = (distanceToCamera - fog_bias);
        float expFog = 1.0 / (exp((max(0.0, (z_depth - uSunDirAndFogStart.w)) * fog_rate)));
        //float height = (dot(fogHeightPlane.xyz, vPosition.xyz) + fogHeightPlane.w);
        //float heightFog = clamp((height * heightRate), 0, 1);
        float heightFog = 1.0;
        expFog = (expFog + heightFog);
        float endFadeFog = clamp(((uFogEnd - distanceToCamera) / (0.699999988 * uFogEnd)), 0.0, 1.0);
        float fog_out = min(expFog, endFadeFog);
        finalColor.rgba = vec4(mix(fogColor.rgb, finalColor.rgb, vec3(fog_out)), finalColor.a);
    }

    //outputColor = blender_srgb_to_framebuffer_space(finalColor);
    finalColor.a = clamp(finalColor.a, 0.0, 1.0);
    outputColor = vec4(finalColor.rgb, finalColor.a);

}

#endif //COMPILING_FS

