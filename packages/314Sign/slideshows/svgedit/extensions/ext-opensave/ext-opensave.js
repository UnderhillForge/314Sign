/* SVG-Edit Extension: Import (Upload) Image - IIFE Format */
(() => {
  const extOpensave = {
    name: 'ext-opensave',
    async init() {
      const svgEditor = this;
      const { svgCanvas } = svgEditor;
      const { $id, $click } = svgCanvas;

      const uploadImageFile = async (file) => {
      const formData = new FormData();
      formData.append("media", file);
      const response = await fetch("/api/slideshows/media/upload", {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error(`Upload failed (${response.status})`);
      }
      const payload = await response.json();
      if (!payload?.success || !payload?.data?.path) {
        throw new Error("Upload failed");
      }
      return payload.data.path;
    };

      const insertImageFromUrl = (url) => {
        const img = new Image();
        img.onload = () => {
          const imgWidth = img.width || 100;
          const imgHeight = img.height || 100;
          
          const newImage = svgCanvas.addSVGElementsFromJson({
            element: "image",
            attr: {
              x: 0,
              y: 0,
              width: imgWidth,
              height: imgHeight,
              id: svgCanvas.getNextId(),
              style: "pointer-events:inherit"
            }
          });
          svgCanvas.setHref(newImage, url);
          svgCanvas.selectOnly([newImage]);
          svgCanvas.alignSelectedElements("m", "page");
          svgCanvas.alignSelectedElements("c", "page");
          if (svgEditor.topPanel?.updateContextPanel) {
            svgEditor.topPanel.updateContextPanel();
          }
        };
        img.src = url;
      };

      const importImage = async (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        let file;
        if (e.type === "drop") {
          file = e.dataTransfer?.files[0];
        } else {
          file = e.currentTarget?.files[0];
        }
        
        if (!file || !file.type.startsWith("image/")) {
          return;
        }
        
        try {
          const uploadedUrl = await uploadImageFile(file);
          insertImageFromUrl(uploadedUrl);
        } catch (error) {
          console.error("Image import failed:", error);
          alert("Image upload failed: " + error.message);
        }
        
        if (e.currentTarget && e.currentTarget.type === "file") {
          e.currentTarget.value = "";
        }
      };
      const imgImport = document.createElement("input");
      imgImport.type = "file";
      imgImport.accept = "image/*";
      imgImport.addEventListener("change", importImage);
      
      if (svgEditor.workarea) {
        svgEditor.workarea.addEventListener("drop", importImage);
      }

      return {
        name: 'Import Image',
        callback() {
          try {
            const mainButton = $id("main_button");
            if (!mainButton) {
              console.warn("main_button not found");
              return;
            }
            
            // Create import menu item
            const importButtonTemplate = '<se-menu-item id="tool_import" label="Import Image" src="importImg.svg"></se-menu-item>';
            
            // Insert at position 4
            svgCanvas.insertChildAtIndex(mainButton, importButtonTemplate, 4);
            
            // Add click handler
            const importBtn = $id("tool_import");
            if (importBtn) {
              console.log("Import button found, adding click handler");
              $click(importBtn, (ev) => {
                imgImport.click();
              });
            } else {
              console.warn("Import button not found after insertion");
            }
          } catch (err) {
            console.error("Error in extension callback:", err);
          }
        }
      };
    }
  };

  // Make extension available
  if (window.svgEditor && typeof window.svgEditor.addExtension === 'function') {
    window.svgEditor.addExtension('ext-opensave', extOpensave);
  } else {
    window.extOpensave = extOpensave;
  }
})();

