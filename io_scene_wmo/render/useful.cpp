// M2

mathfu::vec3 &M2MeshBufferUpdater::getFogColor(EGxBlendEnum blendMode, mathfu::vec3 &originalFogColor) {

    static mathfu::vec3 fog_zero = mathfu::vec3(0,0,0);
    static mathfu::vec3 fog_half = mathfu::vec3(0.5,0.5,0.5);
    static mathfu::vec3 fog_one = mathfu::vec3(1.0,1.0,1.0);

    switch (blendMode) {
        case EGxBlendEnum::GxBlend_Opaque: //Blend_Opaque
        case EGxBlendEnum::GxBlend_AlphaKey : //Blend_AlphaKey
        case EGxBlendEnum::GxBlend_Alpha : //Blend_Alpha
            return originalFogColor;

        case EGxBlendEnum::GxBlend_NoAlphaAdd  : //Blend_NoAlphaAdd
        case EGxBlendEnum::GxBlend_Add : //Blend_Add
            return fog_zero;

        case EGxBlendEnum::GxBlend_Mod: //Blend_Mod
            return fog_one;

        case EGxBlendEnum::GxBlend_Mod2x:
        case EGxBlendEnum::GxBlend_BlendAdd:
            return fog_half;

        default :
            debuglog("Unknown blending mode in M2 file")
            break;
    }

    return originalFogColor;
}


void M2MeshBufferUpdater::fillLights(const M2Object &m2Object, meshWideBlockPS &meshblockPS) {
    bool BCLoginScreenHack = m2Object.m_api->getConfig()->getBCLightHack();
    int lightCount = (int) std::min(m2Object.lights.size(), (size_t) 4);
    for (int j = 0; j < lightCount; j++) {
        std::string uniformName;
        mathfu::vec4 attenVec;
        if (BCLoginScreenHack) {
            attenVec = mathfu::vec4(m2Object.lights[j].attenuation_start, 1.0, m2Object.lights[j].attenuation_end, m2Object.lights.size());
        } else {
//            if ((lights[i].attenuation_end - lights[i].attenuation_start < 0.1)) continue;
//            attenVec = mathfu::vec4(lights[i].attenuation_start, 1.0, lights[i].attenuation_end, lights.size());
            attenVec = mathfu::vec4(m2Object.lights[j].attenuation_start, m2Object.lights[j].diffuse_intensity, m2Object.lights[j].attenuation_end, m2Object.lights.size());
        }

        meshblockPS.pc_lights[j].attenuation = attenVec;//;lights[i].diffuse_color);
        meshblockPS.pc_lights[j].color = m2Object.lights[j].diffuse_color;


//        mathfu::vec4 viewPos = modelView * m2Object.lights[j].position;
        meshblockPS.pc_lights[j].position = m2Object.lights[j].position;
    }
    meshblockPS.LightCount = lightCount;

}

// sorting

void M2Object::sortMaterials(mathfu::mat4 &modelViewMat) {
    if (!m_loaded) return;

    M2Data * m2File = this->m_m2Geom->getM2Data();
    M2SkinProfile * skinData = this->m_skinGeom->getSkinData();

    for (int i = 0; i < this->m_meshArray.size(); i++) {
        //Update info for sorting
        M2MeshBufferUpdater::updateSortData(this->m_meshArray[i], *this, m_materialArray[i], m2File, skinData, modelViewMat);
    }
}

void M2MeshBufferUpdater::updateSortData(HGM2Mesh &hmesh, const M2Object &m2Object, M2MaterialInst &materialData,
                                         const M2Data * m2File, const M2SkinProfile *m2SkinProfile, mathfu::mat4 &modelViewMat) {

    M2Batch *textMaterial = m2SkinProfile->batches.getElement(materialData.texUnitTexIndex);
    M2SkinSection *submesh = m2SkinProfile->submeshes.getElement(textMaterial->skinSectionIndex);

    mathfu::vec4 centerBB = mathfu::vec4(mathfu::vec3(submesh->sortCenterPosition), 1.0);

    const mathfu::mat4 &boneMat = m2Object.bonesMatrices[submesh->centerBoneIndex];
    centerBB = modelViewMat * (boneMat * centerBB);

    float value = centerBB.xyz().Length();

    if (textMaterial->flags & 3) {
        mathfu::vec4 resultPoint;

        if ( value > 0.00000023841858 ) {
            resultPoint = centerBB * (1.0f / value);
        } else {
            resultPoint = centerBB;
        }

        mathfu::mat4 mat4 = modelViewMat * boneMat;
        float dist = mat4.GetColumn(3).xyz().Length();
        float sortDist = dist * submesh->sortRadius;

        resultPoint *= sortDist;

        if (textMaterial->flags & 1) {
            value = (centerBB - resultPoint).xyz().Length();
        } else {
            value = (centerBB + resultPoint).xyz().Length();
        }
    }

    hmesh->setSortDistance(value);


static inline bool sortMeshes(const HGMesh a, const HGMesh b) {
        auto* pA = a.get();
        auto* pB = b.get();

        if (pA->getIsTransparent() > pB->getIsTransparent()) {
            return false;
        }
        if (pA->getIsTransparent() < pB->getIsTransparent()) {
            return true;
        }

        if (pA->getMeshType() > pB->getMeshType()) {
            return false;
        }
        if (pA->getMeshType() < pB->getMeshType()) {
            return true;
        }

        if (pA->m_renderOrder != pB->m_renderOrder ) {
            if (!pA->getIsTransparent()) {
                return pA->m_renderOrder < pB->m_renderOrder;
            } else {
                return pA->m_renderOrder > pB->m_renderOrder;
            }
        }

        if (pA->m_isSkyBox > pB->m_isSkyBox) {
            return true;
        }
        if (pA->m_isSkyBox < pB->m_isSkyBox) {
            return false;
        }

        if (pA->getMeshType() == MeshType::eM2Mesh && pA->getIsTransparent() && pB->getIsTransparent()) {
            if (pA->m_priorityPlane != pB->m_priorityPlane) {
                return pB->m_priorityPlane > pA->m_priorityPlane;
            }

            if (pA->m_sortDistance > pB->m_sortDistance) {
                return true;
            }
            if (pA->m_sortDistance < pB->m_sortDistance) {
                return false;
            }

            if (pA->m_m2Object > pB->m_m2Object) {
                return true;
            }
            if (pA->m_m2Object < pB->m_m2Object) {
                return false;
            }

            if (pB->m_layer != pA->m_layer) {
                return pB->m_layer < pA->m_layer;
            }
        }

        if (pA->getMeshType() == MeshType::eParticleMesh && pB->getMeshType() == MeshType::eParticleMesh) {
            if (pA->m_priorityPlane != pB->m_priorityPlane) {
                return pB->m_priorityPlane > pA->m_priorityPlane;
            }

            if (pA->m_sortDistance > pB->m_sortDistance) {
                return true;
            }
            if (pA->m_sortDistance < pB->m_sortDistance) {
                return false;
            }
        }

        if (pA->m_bindings != pB->m_bindings) {
            return pA->m_bindings > pB->m_bindings;
        }

        if (pA->getGxBlendMode() != pB->getGxBlendMode()) {
            return pA->getGxBlendMode() < pB->getGxBlendMode();
        }

        int minTextureCount = pA->m_textureCount < pB->m_textureCount ? pA->m_textureCount : pB->m_textureCount;
        for (int i = 0; i < minTextureCount; i++) {
            if (pA->m_texture[i] != pB->m_texture[i]) {
                return pA->m_texture[i] < pB->m_texture[i];
            }
        }

        if (pA->m_textureCount != pB->m_textureCount) {
            return pA->m_textureCount < pB->m_textureCount;
        }

        if (pA->m_start != pB->m_start) {
            return pA->m_start < pB->m_start;
        }
        if (pA->m_end != pB->m_end) {
            return pA->m_end < pB->m_end;
        }


        return a > b;
    }


void M2Object::collectMeshes(std::vector<HGMesh> &renderedThisFrame, int renderOrder) {
    if (!m_loaded) return;

    M2SkinProfile* skinData = this->m_skinGeom->getSkinData();

    int minBatch = m_api->getConfig()->getM2MinBatch();
    int maxBatch = std::min(m_api->getConfig()->getM2MaxBatch(), (const int &) this->m_meshArray.size());

    for (int i = minBatch; i < maxBatch; i++) {
        float finalTransparency = M2MeshBufferUpdater::calcFinalTransparency(*this, i, skinData);
        if ((finalTransparency < 0.0001) ) continue;

        this->m_meshArray[i]->setRenderOrder(renderOrder);
        renderedThisFrame.push_back(this->m_meshArray[i]);
    }

//    renderedThisFrame.push_back(occlusionQuery);
}

float M2MeshBufferUpdater::calcFinalTransparency(const M2Object &m2Object, int batchIndex, M2SkinProfile * m2SkinProfile){
    auto textMaterial = m2SkinProfile->batches[batchIndex];
    int renderFlagIndex = textMaterial->materialIndex;

    mathfu::vec4 meshColor = M2Object::getCombinedColor(m2SkinProfile, batchIndex, m2Object.subMeshColors);
    float transparency = M2Object::getTransparency(m2SkinProfile, batchIndex, m2Object.transparencies);
    float finalTransparency = meshColor.w;
    if ( textMaterial->textureCount && !(textMaterial->flags & 0x40)) {
        finalTransparency *= transparency;
    }

	return finalTransparency;

}

enum class MeshType {
    eGeneralMesh = 0,
    eAdtMesh = 1,
    eWmoMesh = 2,
    eOccludingQuery = 3,
    eM2Mesh = 4,
    eParticleMesh = 5,
};

m_isTransparent = m_blendMode > EGxBlendEnum::GxBlend_AlphaKey || !m_depthWrite ;


meshTemplate.blendMode = M2BlendingModeToEGxBlendEnum[material.blending_mode];

