import{$ as e,E as t,I as n,L as r,N as i,Q as a,Rt as o,_ as s,_t as c,at as l,c as u,d,f,g as p,h as m,i as h,it as g,l as _,lt as v,u as y}from"./_plugin-vue_export-helper-_33ZmgFl.js";import{n as b,r as ee,t as x}from"./pairlistConfig-Fwt4Ix4-.js";import{n as te,t as S}from"./TimeRangeSelect-CycwjY7Y.js";import{Jl as C,Ml as w,Nc as T,Ou as E,Pc as D,Tc as O,Tu as k,Wl as A,lc as j,xu as M,yc as N,yu as P}from"./index-kL7y5Hnw.js";import{t as ne}from"./FtPanel-B3Z5pQHi.js";import{t as F}from"./ToolPage-B5SIRryT.js";import{t as I}from"./inputnumber-DjoOzPHO.js";import{t as L}from"./delete-DBHEtBfx.js";import{n as R,t as z}from"./BaseCheckbox-B1z6Bdrx.js";import{t as B}from"./multiselect-Ba7mIuRp.js";import{t as V}from"./ExchangeSelect-Ccs8xyu-.js";var H=D.extend({name:`progressbar`,style:`
    .p-progressbar {
        display: block;
        position: relative;
        overflow: hidden;
        height: dt('progressbar.height');
        background: dt('progressbar.background');
        border-radius: dt('progressbar.border.radius');
    }

    .p-progressbar-value {
        margin: 0;
        background: dt('progressbar.value.background');
    }

    .p-progressbar-label {
        color: dt('progressbar.label.color');
        font-size: dt('progressbar.label.font.size');
        font-weight: dt('progressbar.label.font.weight');
    }

    .p-progressbar-determinate .p-progressbar-value {
        height: 100%;
        width: 0%;
        position: absolute;
        display: none;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        transition: width 1s ease-in-out;
    }

    .p-progressbar-determinate .p-progressbar-label {
        display: inline-flex;
    }

    .p-progressbar-indeterminate .p-progressbar-value::before {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim 2.1s cubic-bezier(0.65, 0.815, 0.735, 0.395) infinite;
    }

    .p-progressbar-indeterminate .p-progressbar-value::after {
        content: '';
        position: absolute;
        background: inherit;
        inset-block-start: 0;
        inset-inline-start: 0;
        inset-block-end: 0;
        will-change: inset-inline-start, inset-inline-end;
        animation: p-progressbar-indeterminate-anim-short 2.1s cubic-bezier(0.165, 0.84, 0.44, 1) infinite;
        animation-delay: 1.15s;
    }

    @keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim {
        0% {
            inset-inline-start: -35%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
        100% {
            inset-inline-start: 100%;
            inset-inline-end: -90%;
        }
    }

    @keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
    @-webkit-keyframes p-progressbar-indeterminate-anim-short {
        0% {
            inset-inline-start: -200%;
            inset-inline-end: 100%;
        }
        60% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
        100% {
            inset-inline-start: 107%;
            inset-inline-end: -8%;
        }
    }
`,classes:{root:function(e){var t=e.instance;return[`p-progressbar p-component`,{"p-progressbar-determinate":t.determinate,"p-progressbar-indeterminate":t.indeterminate}]},value:`p-progressbar-value`,label:`p-progressbar-label`}}),U={name:`ProgressBar`,extends:{name:`BaseProgressBar`,extends:T,props:{value:{type:Number,default:null},mode:{type:String,default:`determinate`},showValue:{type:Boolean,default:!0}},style:H,provide:function(){return{$pcProgressBar:this,$parentInstance:this}}},inheritAttrs:!1,computed:{progressStyle:function(){return{width:this.value+`%`,display:`flex`}},indeterminate:function(){return this.mode===`indeterminate`},determinate:function(){return this.mode===`determinate`},dataP:function(){return w({determinate:this.determinate,indeterminate:this.indeterminate})}}},W=[`aria-valuenow`,`data-p`],G=[`data-p`],K=[`data-p`],q=[`data-p`];function J(e,n,a,s,c,l){return i(),f(`div`,t({role:`progressbar`,class:e.cx(`root`),"aria-valuemin":`0`,"aria-valuenow":e.value,"aria-valuemax":`100`,"data-p":l.dataP},e.ptmi(`root`)),[l.determinate?(i(),f(`div`,t({key:0,class:e.cx(`value`),style:l.progressStyle,"data-p":l.dataP},e.ptm(`value`)),[e.value!=null&&e.value!==0&&e.showValue?(i(),f(`div`,t({key:0,class:e.cx(`label`),"data-p":l.dataP},e.ptm(`label`)),[r(e.$slots,`default`,{},function(){return[m(o(e.value+`%`),1)]})],16,K)):d(``,!0)],16,G)):l.indeterminate?(i(),f(`div`,t({key:1,class:e.cx(`value`),"data-p":l.dataP},e.ptm(`value`)),null,16,q)):d(``,!0)],16,W)}U.render=J;var Y={viewBox:`0 0 24 24`,width:`1.2em`,height:`1.2em`};function X(e,t){return i(),f(`svg`,Y,[...t[0]||=[_(`path`,{fill:`currentColor`,d:`M8 17v-2h8v2zm8-7l-4 4l-4-4h2.5V7h3v3zM5 3h14a2 2 0 0 1 2 2v14c0 1.11-.89 2-2 2H5a2 2 0 0 1-2-2V5c0-1.1.9-2 2-2m0 2v14h14V5z`},null,-1)]])}var Z=l({name:`mdi-download-box-outline`,render:X}),Q={class:`flex flex-row items-end gap-1`},re={class:`ms-2 w-full grow space-y-1`},ie=[`title`],ae={key:1},oe={class:`flex justify-between`},se={key:1},ce={key:2,class:`w-25`},le={key:3,class:`flex flex-col md:flex-row w-full grow gap-2`},ue=s({__name:`BackgroundJobTracking`,setup(e){let{runningJobs:t,clearJobs:r}=C();return(e,s)=>{let l=Z,u=R,g=U,v=L,b=O;return i(),f(`div`,Q,[_(`ul`,re,[(i(!0),f(h,null,n(c(t),(e,t)=>(i(),f(`li`,{key:t,class:`border border-line p-2 rounded-md flex gap-2 items-center`,title:t},[e.taskStatus?.job_category===`download_data`?(i(),y(l,{key:0})):(i(),f(`span`,ae,o(e.taskStatus?.job_category),1)),_(`div`,oe,[e.taskStatus?.status===`success`?(i(),y(u,{key:0,class:`text-ok`,title:``})):(i(),f(`span`,se,o(e.taskStatus?.status),1)),e.taskStatus?.progress?(i(),f(`span`,ce,o(e.taskStatus?.progress),1)):d(``,!0)]),e.taskStatus?.progress?(i(),y(g,{key:2,class:`w-full grow`,value:e.taskStatus?.progress/100*100,"show-progress":``,max:100,striped:``},null,8,[`value`])):d(``,!0),e.taskStatus?.progress_tasks?(i(),f(`div`,le,[(i(!0),f(h,null,n(Object.entries(e.taskStatus?.progress_tasks),([t,n])=>(i(),f(`div`,{key:t,class:`w-full`},[m(o(n.description)+` `,1),p(g,{class:`w-full grow`,value:Math.round(n.progress/n.total*100*100)/100,"show-progress":``,pt:{value:{class:e.taskStatus.status===`success`?`bg-ok`:`bg-warn`}},striped:``},null,8,[`value`,`pt`])]))),128))])):d(``,!0)],8,ie))),128))]),Object.keys(c(t)).length>0?(i(),y(b,{key:0,severity:`secondary`,class:`ms-auto`,onClick:c(r)},{icon:a(()=>[p(v)]),_:1},8,[`onClick`])):d(``,!0)])}}}),de=v([{description:`All USDT Pairs`,pairs:[`.*/USDT`]},{description:`All USDT Futures Pairs`,pairs:[`.*/USDT:USDT`]}]);function fe(){return{pairTemplates:u(()=>de.value.map((e,t)=>({...e,idx:t})))}}var pe={class:`ft-stack`},me={class:`flex mb-3 gap-3 flex-col`},he={class:`flex flex-col gap-3`},ge={class:`flex flex-col lg:flex-row gap-3`},_e={class:`flex-fill`},ve={class:`flex flex-col gap-2`},ye={class:`flex gap-2`},be={class:`flex flex-col gap-1`},xe={class:`flex flex-col gap-1`},Se={class:`flex-fill`},Ce={class:`flex flex-col gap-2`},we={class:`border border-line p-3 rounded-md`},$={class:`flex flex-col gap-2`},Te={class:`flex justify-between items-center`},Ee={key:0},De={key:1,class:`flex items-center gap-2`},Oe={class:`border border-line rounded-md p-3`},ke={class:`mb-2 border border-line rounded-md p-3`},Ae={class:`grid grid-cols md:grid-cols-2 items-center gap-2`},je={class:`mb-2 border border-line rounded-md p-3`},Me=s({__name:`DownloadDataMain`,setup(t){let r=A(),s=x(),l=v([`BTC/USDT`,`ETH/USDT`,``]),u=v([`5m`,`1h`]),C=v({useCustomTimerange:!1,timerange:``,days:30}),{pairTemplates:w}=fe(),T=v({customExchange:!1,selectedExchange:{exchange:`binance`,trade_mode:{margin_mode:P.NONE,trading_mode:M.SPOT}}}),D=v({erase:!1,prepend_data:!1,downloadTrades:!1,candleTypes:[]}),F=v(!1),L=[{text:`Spot`,value:`spot`},{text:`Futures`,value:`futures`},{text:`Funding Rate`,value:`funding_rate`},{text:`Mark`,value:`mark`},{text:`Index`,value:`index`},{text:`Premium Index`,value:`premiumIndex`}];function R(e){l.value.push(...e)}function H(e){l.value=[...e]}async function U(){let e={pairs:l.value.filter(e=>e!==``),timeframes:u.value.filter(e=>e!==``)};C.value.useCustomTimerange&&C.value.timerange?e.timerange=C.value.timerange:e.days=C.value.days,F.value&&(e.erase=D.value.erase,e.download_trades=D.value.downloadTrades,T.value.customExchange&&(e.exchange=T.value.selectedExchange.exchange,e.trading_mode=T.value.selectedExchange.trade_mode.trading_mode,e.margin_mode=T.value.selectedExchange.trade_mode.margin_mode),r.activeBot.botFeatures.downloadDataCandleTypes&&D.value.candleTypes.length>0&&(e.candle_types=D.value.candleTypes),r.activeBot.botFeatures.downloadDataPrepend&&D.value.prepend_data&&(e.prepend_data=!0)),await r.activeBot.startDataDownload(e)}return(t,v)=>{let x=ue,A=b,M=O,P=te,W=z,G=S,K=I,q=j,J=ee,Y=N,X=B,Z=V,Q=ne;return i(),f(`div`,pe,[p(x),p(Q,{title:`Download settings`},{default:a(()=>[_(`div`,me,[_(`div`,he,[_(`div`,ge,[_(`div`,_e,[_(`div`,ve,[v[14]||=_(`div`,{class:`flex justify-between`},[_(`h3`,{class:`ft-label`},`Select Pairs`),_(`span`,{class:`ft-label`},`Pairs from template`)],-1),_(`div`,ye,[p(A,{modelValue:c(l),"onUpdate:modelValue":v[0]||=e=>g(l)?l.value=e:null,placeholder:`Pair`,size:`small`,class:`grow`},null,8,[`modelValue`]),_(`div`,be,[_(`div`,xe,[(i(!0),f(h,null,n(c(w),e=>(i(),y(M,{key:e.idx,severity:`secondary`,title:e.pairs.reduce((e,t)=>`${e}${t}\n`,``),onClick:t=>R(e.pairs)},{default:a(()=>[m(o(e.description),1)]),_:2},1032,[`title`,`onClick`]))),128))]),p(P),p(M,{disabled:c(s).whitelist.length===0,title:`Add all pairs from Pairlist Config - requires the pairlist config to have ran first.`,severity:`secondary`,onClick:v[1]||=e=>H(c(s).whitelist)},{default:a(()=>[...v[13]||=[m(` Use Pairs from Pairlist Config `,-1)]]),_:1},8,[`disabled`])])])])]),_(`div`,Se,[_(`div`,Ce,[v[15]||=_(`h3`,{class:`ft-label`},`Select timeframes`,-1),p(A,{modelValue:c(u),"onUpdate:modelValue":v[2]||=e=>g(u)?u.value=e:null,placeholder:`Timeframe`},null,8,[`modelValue`])])])]),_(`div`,we,[_(`div`,$,[_(`div`,Te,[v[17]||=_(`h3`,{class:`ft-label`},`Time Selection`,-1),p(W,{modelValue:c(C).useCustomTimerange,"onUpdate:modelValue":v[3]||=e=>c(C).useCustomTimerange=e,class:`mb-0`,switch:``},{default:a(()=>[...v[16]||=[m(` Use custom timerange `,-1)]]),_:1},8,[`modelValue`])]),c(C).useCustomTimerange?(i(),f(`div`,Ee,[p(G,{modelValue:c(C).timerange,"onUpdate:modelValue":v[4]||=e=>c(C).timerange=e},null,8,[`modelValue`])])):(i(),f(`div`,De,[v[18]||=_(`label`,{class:`ft-hint`},`Days to download:`,-1),p(K,{modelValue:c(C).days,"onUpdate:modelValue":v[5]||=e=>c(C).days=e,type:`number`,"aria-label":`Days to download`,min:1,step:1,size:`small`},null,8,[`modelValue`])]))])]),_(`div`,Oe,[p(M,{class:`mb-2`,severity:`secondary`,onClick:v[6]||=e=>F.value=!c(F)},{default:a(()=>[v[19]||=m(` Advanced Options `,-1),c(F)?(i(),y(J,{key:1})):(i(),y(q,{key:0}))]),_:1}),p(k,null,{default:a(()=>[e(_(`div`,null,[p(Y,{severity:`info`,class:`mb-2`,closable:!1},{default:a(()=>[...v[20]||=[m(` Advanced options (Erase data, Download trades, and Custom Exchange settings) will only be applied when this section is expanded. `,-1)]]),_:1}),_(`div`,ke,[p(W,{modelValue:c(D).erase,"onUpdate:modelValue":v[7]||=e=>c(D).erase=e,class:`mb-2`},{default:a(()=>[...v[21]||=[m(`Erase existing data`,-1)]]),_:1},8,[`modelValue`]),c(r).activeBot.botFeatures.downloadDataPrepend?(i(),y(W,{key:0,modelValue:c(D).prepend_data,"onUpdate:modelValue":v[8]||=e=>c(D).prepend_data=e,class:`mb-2`},{default:a(()=>[...v[22]||=[m(`Prepend data when downloading`,-1)]]),_:1},8,[`modelValue`])):d(``,!0),p(W,{modelValue:c(D).downloadTrades,"onUpdate:modelValue":v[9]||=e=>c(D).downloadTrades=e,class:`mb-2`},{default:a(()=>[...v[23]||=[m(` Download Trades instead of OHLCV data `,-1)]]),_:1},8,[`modelValue`]),_(`div`,Ae,[c(r).activeBot.botFeatures.downloadDataCandleTypes?(i(),y(X,{key:0,modelValue:c(D).candleTypes,"onUpdate:modelValue":v[10]||=e=>c(D).candleTypes=e,options:L,"option-label":`text`,"option-value":`value`,placeholder:`Select Candle Types`},null,8,[`modelValue`])):d(``,!0),v[24]||=_(`small`,null,`When no candle-type is selected, freqtrade will download the necessary candle types for regular operation automatically.`,-1)])]),_(`div`,je,[p(W,{modelValue:c(T).customExchange,"onUpdate:modelValue":v[11]||=e=>c(T).customExchange=e,class:`mb-2`},{default:a(()=>[...v[25]||=[m(` Custom Exchange `,-1)]]),_:1},8,[`modelValue`]),p(k,{name:`fade`},{default:a(()=>[e(p(Z,{modelValue:c(T).selectedExchange,"onUpdate:modelValue":v[12]||=e=>c(T).selectedExchange=e},null,8,[`modelValue`]),[[E,c(T).customExchange]])]),_:1})])],512),[[E,c(F)]])]),_:1})]),_(`div`,null,[p(M,{severity:`primary`,onClick:U},{default:a(()=>[...v[26]||=[m(`Start Download`,-1)]]),_:1})])])])]),_:1})])}}}),Ne=s({__name:`DownloadDataView`,setup(e){let t=A();return(e,n)=>{let r=Me,o=F;return i(),y(o,{title:`Download data`,description:`Download historic candle data for backtesting.`,"requires-webserver":``,"feature-available":c(t).activeBotorUndefined?.botFeatures.downloadDataView??!0},{default:a(()=>[p(r)]),_:1},8,[`feature-available`])}}});export{Ne as default};
//# sourceMappingURL=DownloadDataView-BjltREnq.js.map