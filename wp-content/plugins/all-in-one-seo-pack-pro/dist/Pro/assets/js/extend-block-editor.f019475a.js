import{x as c,y as w}from"./app-core.339dde72.js";import{h as i}from"./utils.4d62b247.js";import{a as u}from"./icon.3f5d5193.js";import{_ as g}from"./vendor-other.35999c47.js";import"./vendor-vue-ui.33864987.js";import"./vendor-datetime.361c8690.js";import"./vendor-lodash.e0b5303e.js";const{addFilter:k}=window.wp.hooks,{BlockControls:f}=window.wp.blockEditor,{Button:s,ToolbarGroup:p,ToolbarButton:_}=window.wp.components,{Fragment:$,render:y,unmountComponentAtNode:S}=window.wp.element,{createHigherOrderComponent:x}=window.wp.compose,{select:l,useSelect:h}=window.wp.data,b="all-in-one-seo-pack",d={generateWithAI:g("Generate with AI",b),editWithAI:g("Edit with AI",b)};let I=!1;const m=(a,r={})=>{window.aioseoBus.$emit("do-post-settings-main-tab-change",{name:"aiContent"}),a.classList.add("is-busy"),a.disabled=!0;const e=w(),t=c();setTimeout(()=>{t.initiator=r?.initiator,(!t.initiator||!t.initiator.slug)&&t.resetInitiator(),e.isModalOpened="image-generator",a.classList.remove("is-busy"),a.disabled=!1},500)},q=()=>{c().extend.imageBlockToolbar&&(I||(k("editor.BlockEdit","aioseo/extend-image-block-toolbar",x(r=>e=>{const t=e.name==="core/image"&&e.attributes?.url,n=h(o=>!t||!e.attributes?.id?null:o("core").getEntityRecord("postType","attachment",e.attributes.id)||null,[`media-${e.attributes.id}`]);return t?i`
				<${$}>
					<${f}>
						<${p}>
							<${_}
								icon=${u}
								iconSize=${24}
								label=${d.editWithAI}
								onClick=${o=>{m(o.currentTarget,{initiator:{slug:"image-block-toolbar",wpMedia:n}})}}
								style=${{maxHeight:"90%",alignSelf:"center",padding:"0"}}
							/>
						</${p}>
					</${f}>

					<${r} ...${e} />
				</${$}>`:i`<${r} ...${e} />`},"extendImageBlockToolbar")),I=!0))},L=()=>{if(!c().extend.imageBlockPlaceholder)return;const r=l("core/block-editor").getSelectedBlock();if(!r||r.name!=="core/image"||r.attributes?.url)return;const e=document.getElementById(`block-${r.clientId}`),t=e?.querySelector(".components-form-file-upload");if(!t||e?.querySelector(".aioseo-ai-image-generator-btn"))return;const n=document.createElement("div");y(i`
			<${s}
				className=${"aioseo-ai-image-generator-btn"}
				variant=${"secondary"}
				icon=${u}
				iconSize=${"20"}
				__next40pxDefaultSize=${!0}
			>
				${d.generateWithAI}
			</${s}>`,n);const o=n.firstChild?.cloneNode(!0);o&&(t.after(o),o.addEventListener("click",()=>{m(o,{initiator:{slug:"image-block-placeholder"}})})),S(n),n.remove()},N=()=>{if(!c().extend.featuredImageButton||l("core/edit-post").getActiveGeneralSidebarName()!=="edit-post/document")return;if(l("core/editor").getEditedPostAttribute("featured_media")){document.querySelector(".aioseo-ai-image-generator-btn-featured-image")?.remove();return}setTimeout(()=>{const e=document.querySelector(".editor-post-featured-image__container"),t=e?.querySelector("button");if(!t||e?.querySelector(".aioseo-ai-image-generator-btn-featured-image"))return;e.style.display="flex",e.style.gap="8px";const n=document.createElement("div");y(i`
				<${s}
					className=${"aioseo-ai-image-generator-btn-featured-image"}
					variant=${"secondary"}
					icon=${u}
					iconSize=${"20"}
					__next40pxDefaultSize=${!0}
					title=${d.generateWithAI}
				/>`,n);const o=n.firstChild?.cloneNode(!0);o&&(t.after(o),o.addEventListener("click",()=>{m(o,{initiator:{slug:"featured-image-btn"}})})),S(n),n.remove()})};export{N as extendFeaturedImageButton,L as extendImageBlockPlaceholder,q as extendImageBlockToolbar};
