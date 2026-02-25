package com.system.updates.modules

import android.content.Context
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec
import kotlin.math.*

class PolyEngine {
    private val r=SecureRandom()
    private val m=mapOf(
        'a' to "α", 'b' to "β", 'c' to "γ", 'd' to "δ", 'e' to "ε",
        'f' to "ζ", 'g' to "η", 'h' to "θ", 'i' to "ι", 'j' to "κ",
        'k' to "λ", 'l' to "μ", 'm' to "ν", 'n' to "ξ", 'o' to "ο",
        'p' to "π", 'q' to "ρ", 'r' to "σ", 's' to "τ", 't' to "υ",
        'u' to "φ", 'v' to "χ", 'w' to "ψ", 'x' to "ω", 'y' to "ϊ", 'z' to "ϋ"
    )
    private val n=m.entries.associate{ it.value to it.key }

    private fun f(b:ByteArray):ByteArray{
        var x=0x9E3779B9
        val k=ByteArray(4){ (x shr (it*8)).toByte() }
        val o=ByteArray(b.size)
        for(i in b.indices){
            o[i]=(b[i].toInt() xor k[i%4].toInt()).toByte()
        }
        return o
    }

    private fun g(b:ByteArray):ByteArray{
        val l=b.size
        val r=ByteArray(l)
        for(i in 0 until l step 2){
            if(i+1<l){
                r[i]=b[i+1]
                r[i+1]=b[i]
            }else{
                r[i]=b[i]
            }
        }
        return r
    }

    private fun h(b:ByteArray):ByteArray{
        var acc=0
        return b.map{ v->
            acc= (acc+v.toInt()) and 0xFF
            (v.toInt() xor acc).toByte()
        }.toByteArray()
    }

    private fun e(b:ByteArray,ky:ByteArray):ByteArray{
        val c=Cipher.getInstance("AES/GCM/NoPadding")
        val iv=ByteArray(12).also{ r.nextBytes(it) }
        val sks=SecretKeySpec(ky,"AES")
        c.init(Cipher.ENCRYPT_MODE,sks, GCMParameterSpec(128,iv))
        return iv+c.doFinal(b)
    }

    private fun d(b:ByteArray,ky:ByteArray):ByteArray{
        val c=Cipher.getInstance("AES/GCM/NoPadding")
        val iv=b.sliceArray(0..11)
        val ct=b.sliceArray(12 until b.size)
        val sks=SecretKeySpec(ky,"AES")
        c.init(Cipher.DECRYPT_MODE,sks,GCMParameterSpec(128,iv))
        return c.doFinal(ct)
    }

    fun α(ctx:Context,s:String):String{
        val b=s.toByteArray()
        val k=ByteArray(32).also{ r.nextBytes(it) }
        val s1=f(b)
        val s2=g(s1)
        val s3=h(s2)
        val enc=e(s3,k)
        val sb=StringBuilder()
        for(by in enc){
            sb.append(m[by.toInt().mod(26)+97]?:"?")
        }
        return sb.toString()
    }

    fun β(ctx:Context,t:String):String{
        val dec=ByteArray(t.length)
        var i=0
        while(i<t.length){
            val sym=t.substring(i,i+2)
            val ch=n[sym]?:'?'
            dec[i/2]=ch.code.toByte()
            i+=2
        }
        val k=ByteArray(32).also{ r.nextBytes(it) }
        val r1=d(dec,k)
        val r2=h(r1)
        val r3=g(r2)
        val r4=f(r3)
        return String(r4)
    }

    fun γ(ctx:Context,d:ByteArray):Pair<ByteArray,ByteArray>{
        val p1=ByteArray(16).also{ r.nextBytes(it) }
        val p2=ByteArray(16).also{ r.nextBytes(it) }
        val mk=d.copyOf(32)
        for(i in 0..15){
            p2[i]= (p2[i] xor mk[i] xor mk[i+16]).toByte()
        }
        return Pair(p1,p2)
    }

    fun δ(ctx:Context,p1:ByteArray,p2:ByteArray):ByteArray{
        val mk=ByteArray(32)
        for(i in 0..15){
            mk[i]= (p1[i] xor p2[i]).toByte()
        }
        for(i in 16..31){
            mk[i]= (p2[i-16] xor mk[i-16]).toByte()
        }
        return mk
    }

    fun ε(ctx:Context,x:Int):Int{
        var a=x.toLong()
        a=a xor (a shl 13)
        a=a xor (a ushr 17)
        a=a xor (a shl 5)
        return a.toInt()
    }

    fun ζ(ctx:Context,b:ByteArray):List<Int>{
        val l= mutableListOf<Int>()
        for(i in b.indices step 4){
            var acc=0
            for(j in 0..3){
                if(i+j<b.size){
                    acc= acc xor (b[i+j].toInt() shl (j*8))
                }
            }
            l.add(acc)
        }
        return l
    }

    fun η(ctx:Context,l:List<Int>):ByteArray{
        val ba=ByteArray(l.size*4)
        for((idx,v) in l.withIndex()){
            for(j in 0..3){
                if(idx*4+j<ba.size){
                    ba[idx*4+j]= (v shr (j*8) and 0xFF).toByte()
                }
            }
        }
        return ba
    }

    fun θ(ctx:Context,s:String):String{
        val b=s.toByteArray()
        val r1=ζ(ctx,b)
        val r2=r1.map{ ε(ctx,it) }
        val r3=η(ctx,r2)
        return String(r3)
    }
}