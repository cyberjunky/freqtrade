import{$ as e,B as t,L as n,N as r,Pt as i,Q as a,R as o,Rt as s,T as c,c as l,d as u,h as d,l as f,u as p}from"./runtime-core.esm-bundler-C7KLiCKn.js";import{ar as m,cr as h,ct as g,nn as _,on as v,sn as y,tn as b,tr as x}from"./index-CzVFiSqE.js";import{t as S}from"./plus-DdQKN6KZ.js";var C=y.extend({name:`panel`,style:`
    .p-panel {
        display: block;
        border: 1px solid dt('panel.border.color');
        border-radius: dt('panel.border.radius');
        background: dt('panel.background');
        color: dt('panel.color');
    }

    .p-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: dt('panel.header.padding');
        background: dt('panel.header.background');
        color: dt('panel.header.color');
        border-style: solid;
        border-width: dt('panel.header.border.width');
        border-color: dt('panel.header.border.color');
        border-radius: dt('panel.header.border.radius');
    }

    .p-panel-toggleable .p-panel-header {
        padding: dt('panel.toggleable.header.padding');
    }

    .p-panel-title {
        line-height: 1;
        font-weight: dt('panel.title.font.weight');
    }

    .p-panel-content-container {
        display: grid;
        grid-template-rows: 1fr;
    }

    .p-panel-content-wrapper {
        min-height: 0;
    }

    .p-panel-content {
        padding: dt('panel.content.padding');
    }

    .p-panel-footer {
        padding: dt('panel.footer.padding');
    }
`,classes:{root:function(e){return[`p-panel p-component`,{"p-panel-toggleable":e.props.toggleable}]},header:`p-panel-header`,title:`p-panel-title`,headerActions:`p-panel-header-actions`,pcToggleButton:`p-panel-toggle-button`,contentContainer:`p-panel-content-container`,contentWrapper:`p-panel-content-wrapper`,content:`p-panel-content`,footer:`p-panel-footer`}}),w={name:`Panel`,extends:{name:`BasePanel`,extends:v,props:{header:String,toggleable:Boolean,collapsed:Boolean,toggleButtonProps:{type:Object,default:function(){return{severity:`secondary`,text:!0,rounded:!0}}}},style:C,provide:function(){return{$pcPanel:this,$parentInstance:this}}},inheritAttrs:!1,emits:[`update:collapsed`,`toggle`],data:function(){return{d_collapsed:this.collapsed}},watch:{collapsed:function(e){this.d_collapsed=e}},methods:{toggle:function(e){this.d_collapsed=!this.d_collapsed,this.$emit(`update:collapsed`,this.d_collapsed),this.$emit(`toggle`,{originalEvent:e,value:this.d_collapsed})},onKeyDown:function(e){(e.code===`Enter`||e.code===`NumpadEnter`||e.code===`Space`)&&(this.toggle(e),e.preventDefault())}},computed:{buttonAriaLabel:function(){return this.toggleButtonProps&&this.toggleButtonProps.ariaLabel?this.toggleButtonProps.ariaLabel:this.header},dataP:function(){return x({toggleable:this.toggleable})}},components:{PlusIcon:S,MinusIcon:g,Button:b},directives:{ripple:_}},T=[`data-p`],E=[`data-p`],D=[`id`],O=[`id`,`aria-labelledby`];function k(g,_,v,y,b,x){var S=o(`Button`);return r(),u(`div`,c({class:g.cx(`root`),"data-p":x.dataP},g.ptmi(`root`)),[l(`div`,c({class:g.cx(`header`),"data-p":x.dataP},g.ptm(`header`)),[n(g.$slots,`header`,{id:g.$id+`_header`,class:i(g.cx(`title`)),collapsed:b.d_collapsed},function(){return[g.header?(r(),u(`span`,c({key:0,id:g.$id+`_header`,class:g.cx(`title`)},g.ptm(`title`)),s(g.header),17,D)):p(``,!0)]}),l(`div`,c({class:g.cx(`headerActions`)},g.ptm(`headerActions`)),[n(g.$slots,`icons`),g.toggleable?n(g.$slots,`togglebutton`,{key:0,collapsed:b.d_collapsed,toggleCallback:function(e){return x.toggle(e)},keydownCallback:function(e){return x.onKeyDown(e)}},function(){return[d(S,c({id:g.$id+`_header`,class:g.cx(`pcToggleButton`),"aria-label":x.buttonAriaLabel,"aria-controls":g.$id+`_content`,"aria-expanded":!b.d_collapsed,unstyled:g.unstyled,onClick:_[0]||=function(e){return x.toggle(e)},onKeydown:_[1]||=function(e){return x.onKeyDown(e)}},g.toggleButtonProps,{pt:g.ptm(`pcToggleButton`)}),{icon:a(function(e){return[n(g.$slots,g.$slots.toggleicon?`toggleicon`:`togglericon`,{collapsed:b.d_collapsed},function(){return[(r(),f(t(b.d_collapsed?`PlusIcon`:`MinusIcon`),c({class:e.class},g.ptm(`pcToggleButton`).icon),null,16,[`class`]))]})]}),_:3},16,[`id`,`class`,`aria-label`,`aria-controls`,`aria-expanded`,`unstyled`,`pt`])]}):p(``,!0)],16)],16,E),d(m,c({name:`p-collapsible`},g.ptm(`transition`)),{default:a(function(){return[e(l(`div`,c({id:g.$id+`_content`,class:g.cx(`contentContainer`),role:`region`,"aria-labelledby":g.$id+`_header`},g.ptm(`contentContainer`)),[l(`div`,c({class:g.cx(`contentWrapper`)},g.ptm(`contentWrapper`)),[l(`div`,c({class:g.cx(`content`)},g.ptm(`content`)),[n(g.$slots,`default`)],16),g.$slots.footer?(r(),u(`div`,c({key:0,class:g.cx(`footer`)},g.ptm(`footer`)),[n(g.$slots,`footer`)],16)):p(``,!0)],16)],16,O),[[h,!b.d_collapsed]])]}),_:3},16)],16,T)}w.render=k;export{w as t};
//# sourceMappingURL=panel-CjiyjFnc.js.map