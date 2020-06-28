#ifdef COMPILING_VS

/* vertex shader code */

in vec3 aPosition;
in vec3 aNormal;

// Whole model
uniform mat4 uViewProjectionMatrix;
uniform mat4 uPlacementMatrix;

//Individual meshes
uniform vec4 color_Transparency;

//Shader output
out vec3 vPosition;
out vec3 vNormal;


void main() {

    vec4 aPositionVec4 = vec4(aPosition, 1.0f);

    mat3 viewModelMatTransposed = mat3(uViewProjectionMatrix);
    mat4 cameraMatrix = uViewProjectionMatrix;
    vec4 cameraPoint = cameraMatrix * (uPlacementMatrix * aPositionVec4);

    vec3 normal = normalize(viewModelMatTransposed * (mat3(uPlacementMatrix) * aNormal));

    vNormal = normal;
    vPosition = cameraPoint.xyz;

    gl_Position = cameraPoint;

}

#endif //COMPILING_VS


#ifdef COMPILING_FS

struct LocalLight
{
    vec4 color;
    vec4 position;
    vec4 attenuation;
};

in vec3 vPosition;
in vec3 vNormal;


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

    vec4 finalColor = vec4(0);
    vec4 meshResColor = vec4(0.5, 0.5, 0.5, 1.0);
    vec4 vDiffuseColor = meshResColor;

    vec3 accumLight;
    if ((UnFogged_IsAffectedByLight_LightCount.y == 1)) {
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

    //Combiners_Opaque
    matDiffuse = vDiffuseColor.rgb * 2.000000;
    opacity = vDiffuseColor.a;
    finalOpacity = opacity * visParams.r;

    finalColor = vec4(makeDiffTerm(matDiffuse, accumLight) + specular, finalOpacity);

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
