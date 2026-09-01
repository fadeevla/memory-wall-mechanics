; ModuleID = 'findDuplicate_bit_numba'
source_filename = "<string>"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.const.findDuplicate_bit_numba = internal constant [24 x i8] c"findDuplicate_bit_numba\00"
@_ZN08NumbaEnv14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE = common local_unnamed_addr global ptr null
@".const.missing Environment: _ZN08NumbaEnv14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE" = internal constant [175 x i8] c"missing Environment: _ZN08NumbaEnv14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE\00"
@PyExc_TypeError = external global i8
@".const.can't unbox array from PyObject into native value.  The object maybe of a different type" = internal constant [89 x i8] c"can't unbox array from PyObject into native value.  The object maybe of a different type\00"
@".const.unknown error when calling native function" = internal constant [43 x i8] c"unknown error when calling native function\00"
@PyExc_RuntimeError = external global i8
@PyExc_StopIteration = external global i8
@PyExc_SystemError = external global i8
@".const.unknown error when calling native function.2" = internal constant [43 x i8] c"unknown error when calling native function\00"
@".const.<numba.core.cpu.CPUContext>" = internal constant [28 x i8] c"<numba.core.cpu.CPUContext>\00"
@_ZN08NumbaEnv5numba7cpython8builtins6ol_max12_3clocals_3e4implB2v2B42c8tJTIeFIjxB2IKSgI4CrvQClcaMQ5hEEUSJJgA_3dE15StarArgUniTupleIxLi2EE = common local_unnamed_addr global ptr null

define noundef range(i32 -1, -2) i32 @_ZN14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE(ptr noalias writeonly captures(none) %retptr, ptr noalias readnone captures(none) %excinfo, ptr %arg.arr.0, ptr readnone captures(none) %arg.arr.1, i64 %arg.arr.2, i64 %arg.arr.3, ptr readonly captures(none) %arg.arr.4, i64 %arg.arr.5.0, i64 %arg.arr.6.0) local_unnamed_addr {
B0:
  %arg.arr.5.0.fr = freeze i64 %arg.arr.5.0
  %.45 = icmp sgt i64 %arg.arr.5.0.fr, 1
  br i1 %.45, label %B34.preheader, label %common.ret

B34.preheader:                                    ; preds = %B0
  %const = bitcast i64 9223372036854775792 to i64
  %.28 = add nsw i64 %arg.arr.5.0.fr, -1
  %0 = lshr i64 %.28, 1
  %1 = tail call range(i64 1, 65) i64 @llvm.ctlz.i64(i64 %0, i1 false)
  %2 = sub nuw nsw i64 64, %1
  %n.vec = and i64 %arg.arr.5.0.fr, %const
  %const_mat = add i64 %const, 12
  %n.vec12 = and i64 %arg.arr.5.0.fr, %const_mat
  br label %iter.check

common.ret:                                       ; preds = %46, %B0
  %duplicate.2.0.lcssa = phi i64 [ 0, %B0 ], [ %spec.select.us, %46 ]
  store i64 %duplicate.2.0.lcssa, ptr %retptr, align 8
  ret i32 0

iter.check:                                       ; preds = %B34.preheader, %46
  %duplicate.2.0184.us = phi i64 [ %spec.select.us, %46 ], [ 0, %B34.preheader ]
  %.159172182.us = phi i64 [ %.166.us, %46 ], [ 0, %B34.preheader ]
  %3 = icmp ult i64 %arg.arr.5.0.fr, 4
  br i1 %3, label %B162.us.preheader, label %vector.main.loop.iter.check

vector.main.loop.iter.check:                      ; preds = %iter.check
  %4 = icmp ult i64 %arg.arr.5.0.fr, 16
  br i1 %4, label %vec.epilog.ph, label %vector.ph

vector.ph:                                        ; preds = %vector.main.loop.iter.check
  %broadcast.splatinsert = insertelement <4 x i64> poison, i64 %.159172182.us, i64 0
  %broadcast.splat = shufflevector <4 x i64> %broadcast.splatinsert, <4 x i64> poison, <4 x i32> zeroinitializer
  br label %vector.body

vector.body:                                      ; preds = %vector.body, %vector.ph
  %index = phi i64 [ 0, %vector.ph ], [ %index.next, %vector.body ]
  %vec.phi = phi <4 x i64> [ zeroinitializer, %vector.ph ], [ %17, %vector.body ]
  %vec.phi3 = phi <4 x i64> [ zeroinitializer, %vector.ph ], [ %18, %vector.body ]
  %vec.phi4 = phi <4 x i64> [ zeroinitializer, %vector.ph ], [ %19, %vector.body ]
  %vec.phi5 = phi <4 x i64> [ zeroinitializer, %vector.ph ], [ %20, %vector.body ]
  %sunkaddr = mul i64 %index, 4
  %sunkaddr47 = getelementptr i8, ptr %arg.arr.4, i64 %sunkaddr
  %wide.load = load <4 x i32>, ptr %sunkaddr47, align 4
  %sunkaddr48 = mul i64 %index, 4
  %sunkaddr49 = getelementptr i8, ptr %arg.arr.4, i64 %sunkaddr48
  %sunkaddr50 = getelementptr i8, ptr %sunkaddr49, i64 16
  %wide.load6 = load <4 x i32>, ptr %sunkaddr50, align 4
  %sunkaddr51 = mul i64 %index, 4
  %sunkaddr52 = getelementptr i8, ptr %arg.arr.4, i64 %sunkaddr51
  %sunkaddr53 = getelementptr i8, ptr %sunkaddr52, i64 32
  %wide.load7 = load <4 x i32>, ptr %sunkaddr53, align 4
  %sunkaddr54 = mul i64 %index, 4
  %sunkaddr55 = getelementptr i8, ptr %arg.arr.4, i64 %sunkaddr54
  %sunkaddr56 = getelementptr i8, ptr %sunkaddr55, i64 48
  %wide.load8 = load <4 x i32>, ptr %sunkaddr56, align 4
  %5 = sext <4 x i32> %wide.load to <4 x i64>
  %6 = sext <4 x i32> %wide.load6 to <4 x i64>
  %7 = sext <4 x i32> %wide.load7 to <4 x i64>
  %8 = sext <4 x i32> %wide.load8 to <4 x i64>
  %9 = lshr <4 x i64> %5, %broadcast.splat
  %10 = lshr <4 x i64> %6, %broadcast.splat
  %11 = lshr <4 x i64> %7, %broadcast.splat
  %12 = lshr <4 x i64> %8, %broadcast.splat
  %13 = and <4 x i64> %9, splat (i64 1)
  %14 = and <4 x i64> %10, splat (i64 1)
  %15 = and <4 x i64> %11, splat (i64 1)
  %16 = and <4 x i64> %12, splat (i64 1)
  %17 = add <4 x i64> %13, %vec.phi
  %18 = add <4 x i64> %14, %vec.phi3
  %19 = add <4 x i64> %15, %vec.phi4
  %20 = add <4 x i64> %16, %vec.phi5
  %index.next = add nuw i64 %index, 16
  %21 = icmp eq i64 %n.vec, %index.next
  br i1 %21, label %middle.block, label %vector.body, !llvm.loop !0

middle.block:                                     ; preds = %vector.body
  %22 = icmp eq i64 %arg.arr.5.0.fr, %n.vec
  %bin.rdx = add <4 x i64> %18, %17
  %bin.rdx9 = add <4 x i64> %19, %bin.rdx
  %bin.rdx10 = add <4 x i64> %20, %bin.rdx9
  %rdx.shuf = shufflevector <4 x i64> %bin.rdx10, <4 x i64> poison, <4 x i32> <i32 2, i32 3, i32 poison, i32 poison>
  %bin.rdx40 = add <4 x i64> %bin.rdx10, %rdx.shuf
  %rdx.shuf41 = shufflevector <4 x i64> %bin.rdx40, <4 x i64> poison, <4 x i32> <i32 1, i32 poison, i32 poison, i32 poison>
  %bin.rdx42 = add <4 x i64> %bin.rdx40, %rdx.shuf41
  %23 = extractelement <4 x i64> %bin.rdx42, i32 0
  br i1 %22, label %B160.B186_crit_edge.us, label %vec.epilog.iter.check

vec.epilog.iter.check:                            ; preds = %middle.block
  %24 = and i64 %arg.arr.5.0.fr, 12
  %25 = icmp eq i64 %24, 0
  br i1 %25, label %B162.us.preheader, label %vec.epilog.ph, !prof !3

vec.epilog.ph:                                    ; preds = %vector.main.loop.iter.check, %vec.epilog.iter.check
  %vec.epilog.resume.val = phi i64 [ %n.vec, %vec.epilog.iter.check ], [ 0, %vector.main.loop.iter.check ]
  %bc.merge.rdx = phi i64 [ %23, %vec.epilog.iter.check ], [ 0, %vector.main.loop.iter.check ]
  %26 = insertelement <4 x i64> <i64 poison, i64 0, i64 0, i64 0>, i64 %bc.merge.rdx, i64 0
  %broadcast.splatinsert13 = insertelement <4 x i64> poison, i64 %.159172182.us, i64 0
  %broadcast.splat14 = shufflevector <4 x i64> %broadcast.splatinsert13, <4 x i64> poison, <4 x i32> zeroinitializer
  br label %vec.epilog.vector.body

vec.epilog.vector.body:                           ; preds = %vec.epilog.vector.body, %vec.epilog.ph
  %index15 = phi i64 [ %vec.epilog.resume.val, %vec.epilog.ph ], [ %index.next18, %vec.epilog.vector.body ]
  %vec.phi16 = phi <4 x i64> [ %26, %vec.epilog.ph ], [ %31, %vec.epilog.vector.body ]
  %27 = shl i64 %index15, 2
  %scevgep38 = getelementptr i8, ptr %arg.arr.4, i64 %27
  %wide.load17 = load <4 x i32>, ptr %scevgep38, align 4
  %28 = sext <4 x i32> %wide.load17 to <4 x i64>
  %29 = lshr <4 x i64> %28, %broadcast.splat14
  %30 = and <4 x i64> %29, splat (i64 1)
  %31 = add <4 x i64> %30, %vec.phi16
  %index.next18 = add nuw i64 %index15, 4
  %32 = icmp eq i64 %n.vec12, %index.next18
  br i1 %32, label %vec.epilog.middle.block, label %vec.epilog.vector.body, !llvm.loop !4

vec.epilog.middle.block:                          ; preds = %vec.epilog.vector.body
  %33 = icmp eq i64 %arg.arr.5.0.fr, %n.vec12
  %rdx.shuf43 = shufflevector <4 x i64> %31, <4 x i64> poison, <4 x i32> <i32 2, i32 3, i32 poison, i32 poison>
  %bin.rdx44 = add <4 x i64> %31, %rdx.shuf43
  %rdx.shuf45 = shufflevector <4 x i64> %bin.rdx44, <4 x i64> poison, <4 x i32> <i32 1, i32 poison, i32 poison, i32 poison>
  %bin.rdx46 = add <4 x i64> %bin.rdx44, %rdx.shuf45
  %34 = extractelement <4 x i64> %bin.rdx46, i32 0
  br i1 %33, label %B160.B186_crit_edge.us, label %B162.us.preheader

B162.us.preheader:                                ; preds = %iter.check, %vec.epilog.iter.check, %vec.epilog.middle.block
  %count_nums.2.1168.us.ph = phi i64 [ 0, %iter.check ], [ %23, %vec.epilog.iter.check ], [ %34, %vec.epilog.middle.block ]
  %.424164166.us.ph = phi i64 [ 0, %iter.check ], [ %n.vec, %vec.epilog.iter.check ], [ %n.vec12, %vec.epilog.middle.block ]
  br label %B162.us

B162.us:                                          ; preds = %B162.us.preheader, %B162.us
  %count_nums.2.1168.us = phi i64 [ %.491.us, %B162.us ], [ %count_nums.2.1168.us.ph, %B162.us.preheader ]
  %.424164166.us = phi i64 [ %.431.us, %B162.us ], [ %.424164166.us.ph, %B162.us.preheader ]
  %.431.us = add nuw nsw i64 %.424164166.us, 1
  %35 = shl i64 %.424164166.us, 2
  %scevgep39 = getelementptr i8, ptr %arg.arr.4, i64 %35
  %.485.us = load i32, ptr %scevgep39, align 4
  %.487.us = sext i32 %.485.us to i64
  %.488161.us = lshr i64 %.487.us, %.159172182.us
  %.489.us = and i64 %.488161.us, 1
  %.491.us = add nuw nsw i64 %.489.us, %count_nums.2.1168.us
  %exitcond209.not = icmp eq i64 %arg.arr.5.0.fr, %.431.us
  br i1 %exitcond209.not, label %B160.B186_crit_edge.us, label %B162.us, !llvm.loop !5

B160.B186_crit_edge.us:                           ; preds = %B162.us, %vec.epilog.middle.block, %middle.block
  %.491.us.lcssa = phi i64 [ %34, %vec.epilog.middle.block ], [ %23, %middle.block ], [ %.491.us, %B162.us ]
  %.166.us = add nuw nsw i64 %.159172182.us, 1
  %.195.us = shl nuw i64 1, %.159172182.us
  %.201.us = shl nuw i64 2, %.159172182.us
  %36 = or i64 %arg.arr.5.0.fr, %.201.us
  %37 = and i64 %36, -4294967296
  %38 = icmp eq i64 %37, 0
  br i1 %38, label %39, label %44

39:                                               ; preds = %B160.B186_crit_edge.us
  %40 = trunc i64 %.201.us to i32
  %41 = trunc i64 %arg.arr.5.0.fr to i32
  %42 = urem i32 %41, %40
  %43 = zext i32 %42 to i64
  br label %46

44:                                               ; preds = %B160.B186_crit_edge.us
  %45 = srem i64 %arg.arr.5.0.fr, %.201.us
  br label %46

46:                                               ; preds = %44, %39
  %47 = phi i64 [ %43, %39 ], [ %45, %44 ]
  %.272.us = xor i64 %47, %.201.us
  %.273.us = icmp slt i64 %.272.us, 0
  %.274.us = icmp ne i64 %47, 0
  %.275.us = and i1 %.274.us, %.273.us
  %.282.us = select i1 %.275.us, i64 %.201.us, i64 0
  %.262.1.us = sub i64 %47, %.195.us
  %.293.us = add i64 %.262.1.us, %.282.us
  %.13.i = tail call i64 @llvm.smax.i64(i64 %.293.us, i64 0)
  %.226.us199 = lshr i64 %arg.arr.5.0.fr, %.166.us
  %.236.us = sext i1 %.275.us to i64
  %.215.1.us = add nsw i64 %.226.us199, %.236.us
  %.292159.us = shl i64 %.215.1.us, %.159172182.us
  %.322.us = add nsw i64 %.292159.us, %.13.i
  %.507.us = icmp sgt i64 %.491.us.lcssa, %.322.us
  %.515.us = select i1 %.507.us, i64 %.195.us, i64 0
  %spec.select.us = or i64 %.515.us, %duplicate.2.0184.us
  %exitcond210.not = icmp eq i64 %.159172182.us, %2
  br i1 %exitcond210.not, label %common.ret, label %iter.check
}

define ptr @_ZN7cpython14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE(ptr readnone captures(none) %py_closure, ptr %py_args, ptr readnone captures(none) %py_kws) local_unnamed_addr {
entry:
  %.5 = alloca ptr, align 8
  %.6 = call i32 (ptr, ptr, i64, i64, ...) @PyArg_UnpackTuple(ptr %py_args, ptr nonnull @.const.findDuplicate_bit_numba, i64 1, i64 1, ptr nonnull %.5)
  %.7 = icmp eq i32 %.6, 0
  %.19 = alloca { ptr, ptr, i64, i64, ptr, [1 x i64], [1 x i64] }, align 8
  %.41 = alloca i64, align 8
  br i1 %.7, label %common.ret, label %entry.endif, !prof !6

common.ret:                                       ; preds = %entry.endif.endif.if, %entry.endif.endif.endif.endif.endif.endif, %entry.endif.endif.endif.endif.endif.endif.if, %entry.endif.endif.endif.endif.endif.endif.endif.endif, %entry, %entry.endif.endif.endif.endif.if.endif, %entry.endif.if
  %common.ret.op = phi ptr [ null, %entry.endif.endif.endif.endif.endif.endif.endif.endif ], [ null, %entry ], [ null, %entry.endif.if ], [ null, %entry.endif.endif.endif.endif.endif.endif.if ], [ %.67, %entry.endif.endif.endif.endif.if.endif ], [ null, %entry.endif.endif.if ], [ null, %entry.endif.endif.endif.endif.endif.endif ]
  ret ptr %common.ret.op

entry.endif:                                      ; preds = %entry
  %.11 = load ptr, ptr @_ZN08NumbaEnv14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE, align 8
  %.14 = icmp eq ptr %.11, null
  br i1 %.14, label %entry.endif.if, label %entry.endif.endif, !prof !6

entry.endif.if:                                   ; preds = %entry.endif
  call void @PyErr_SetString(ptr nonnull @PyExc_RuntimeError, ptr nonnull @".const.missing Environment: _ZN08NumbaEnv14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE")
  br label %common.ret

entry.endif.endif:                                ; preds = %entry.endif
  %.18 = load ptr, ptr %.5, align 8
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(56) %.19, i8 0, i64 56, i1 false)
  %.23 = call i32 @NRT_adapt_ndarray_from_python(ptr %.18, ptr nonnull %.19)
  %sunkaddr = getelementptr inbounds i8, ptr %.19, i64 24
  %.27 = load i64, ptr %sunkaddr, align 8
  %.28 = icmp ne i64 %.27, 4
  %.29 = icmp ne i32 %.23, 0
  %.30 = or i1 %.29, %.28
  br i1 %.30, label %entry.endif.endif.if, label %entry.endif.endif.endif.endif, !prof !6

entry.endif.endif.if:                             ; preds = %entry.endif.endif
  call void @PyErr_SetString(ptr nonnull @PyExc_TypeError, ptr nonnull @".const.can't unbox array from PyObject into native value.  The object maybe of a different type")
  br label %common.ret

entry.endif.endif.endif.endif:                    ; preds = %entry.endif.endif
  %.34.fca.0.load = load ptr, ptr %.19, align 8
  %sunkaddr1 = getelementptr inbounds i8, ptr %.19, i64 32
  %.34.fca.4.load = load ptr, ptr %sunkaddr1, align 8
  %sunkaddr2 = getelementptr inbounds i8, ptr %.19, i64 40
  %.34.fca.5.0.load = load i64, ptr %sunkaddr2, align 8
  store i64 0, ptr %.41, align 8
  %.47 = call i32 @_ZN14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE(ptr nonnull %.41, ptr nonnull poison, ptr %.34.fca.0.load, ptr poison, i64 poison, i64 poison, ptr %.34.fca.4.load, i64 %.34.fca.5.0.load, i64 poison) #3
  %.57 = load i64, ptr %.41, align 8
  call void @NRT_decref(ptr %.34.fca.0.load)
  %cond = icmp eq i32 %.47, 0
  br i1 %cond, label %entry.endif.endif.endif.endif.if.endif, label %entry.endif.endif.endif.endif.endif, !prof !7

entry.endif.endif.endif.endif.endif:              ; preds = %entry.endif.endif.endif.endif
  %.55 = icmp sgt i32 %.47, 0
  br i1 %.55, label %entry.endif.endif.endif.endif.endif.if, label %entry.endif.endif.endif.endif.endif.endif

entry.endif.endif.endif.endif.if.endif:           ; preds = %entry.endif.endif.endif.endif
  %.67 = call ptr @PyLong_FromLongLong(i64 %.57)
  br label %common.ret

entry.endif.endif.endif.endif.endif.if:           ; preds = %entry.endif.endif.endif.endif.endif
  call void @PyErr_Clear()
  unreachable

entry.endif.endif.endif.endif.endif.endif:        ; preds = %entry.endif.endif.endif.endif.endif
  switch i32 %.47, label %entry.endif.endif.endif.endif.endif.endif.endif.endif [
    i32 -3, label %entry.endif.endif.endif.endif.endif.endif.if
    i32 -1, label %common.ret
  ]

entry.endif.endif.endif.endif.endif.endif.if:     ; preds = %entry.endif.endif.endif.endif.endif.endif
  call void @PyErr_SetNone(ptr nonnull @PyExc_StopIteration)
  br label %common.ret

entry.endif.endif.endif.endif.endif.endif.endif.endif: ; preds = %entry.endif.endif.endif.endif.endif.endif
  call void @PyErr_SetString(ptr nonnull @PyExc_SystemError, ptr nonnull @".const.unknown error when calling native function")
  br label %common.ret
}

declare i32 @PyArg_UnpackTuple(ptr, ptr, i64, i64, ...) local_unnamed_addr

declare void @PyErr_SetString(ptr, ptr) local_unnamed_addr

; Function Attrs: mustprogress nocallback nofree nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr writeonly captures(none), i8, i64, i1 immarg) #0

declare i32 @NRT_adapt_ndarray_from_python(ptr captures(none), ptr captures(none)) local_unnamed_addr

declare ptr @PyLong_FromLongLong(i64) local_unnamed_addr

declare void @PyErr_Clear() local_unnamed_addr

declare void @PyErr_SetNone(ptr) local_unnamed_addr

define i64 @cfunc._ZN14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE({ ptr, ptr, i64, i64, ptr, [1 x i64], [1 x i64] } %.1) local_unnamed_addr {
entry:
  %.3 = alloca i64, align 8
  store i64 0, ptr %.3, align 8
  %extracted.meminfo = extractvalue { ptr, ptr, i64, i64, ptr, [1 x i64], [1 x i64] } %.1, 0
  %extracted.data = extractvalue { ptr, ptr, i64, i64, ptr, [1 x i64], [1 x i64] } %.1, 4
  %extracted.shape = extractvalue { ptr, ptr, i64, i64, ptr, [1 x i64], [1 x i64] } %.1, 5
  %.7 = extractvalue [1 x i64] %extracted.shape, 0
  %.9 = call i32 @_ZN14duplicate_find10algorithms9bit_numba23findDuplicate_bit_numbaB2v1B38c8tJTIeFIjxB2IKSgI4CrvQClQZ6FczSBAA_3dE5ArrayIiLi1E1C7mutable7alignedE(ptr nonnull %.3, ptr nonnull poison, ptr %extracted.meminfo, ptr poison, i64 poison, i64 poison, ptr %extracted.data, i64 %.7, i64 poison) #3
  %.19 = load i64, ptr %.3, align 8
  %.21 = alloca i32, align 4
  store i32 0, ptr %.21, align 4
  %cond = icmp eq i32 %.9, 0
  br i1 %cond, label %common.ret, label %entry.if, !prof !7

entry.if:                                         ; preds = %entry
  %.17 = icmp sgt i32 %.9, 0
  call void @numba_gil_ensure(ptr nonnull %.21)
  br i1 %.17, label %entry.if.if, label %entry.if.endif

common.ret:                                       ; preds = %entry, %.24
  ret i64 %.19

.24:                                              ; preds = %entry.if.endif, %entry.if.endif.endif.endif, %entry.if.endif.if
  %.72 = call ptr @PyUnicode_FromString(ptr nonnull @".const.<numba.core.cpu.CPUContext>")
  call void @PyErr_WriteUnraisable(ptr %.72)
  call void @Py_DecRef(ptr %.72)
  call void @numba_gil_release(ptr nonnull %.21)
  br label %common.ret

entry.if.if:                                      ; preds = %entry.if
  call void @PyErr_Clear()
  unreachable

entry.if.endif:                                   ; preds = %entry.if
  switch i32 %.9, label %entry.if.endif.endif.endif [
    i32 -3, label %entry.if.endif.if
    i32 -1, label %.24
  ]

entry.if.endif.if:                                ; preds = %entry.if.endif
  call void @PyErr_SetNone(ptr nonnull @PyExc_StopIteration)
  br label %.24

entry.if.endif.endif.endif:                       ; preds = %entry.if.endif
  call void @PyErr_SetString(ptr nonnull @PyExc_SystemError, ptr nonnull @".const.unknown error when calling native function.2")
  br label %.24
}

declare void @numba_gil_ensure(ptr) local_unnamed_addr

declare ptr @PyUnicode_FromString(ptr) local_unnamed_addr

declare void @PyErr_WriteUnraisable(ptr) local_unnamed_addr

declare void @Py_DecRef(ptr) local_unnamed_addr

declare void @numba_gil_release(ptr) local_unnamed_addr

; Function Attrs: mustprogress nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smax.i64(i64, i64) #1

; Function Attrs: mustprogress nofree noinline norecurse nounwind willreturn memory(argmem: readwrite)
define linkonce_odr void @NRT_incref(ptr captures(address_is_null) %.1) local_unnamed_addr #2 {
.3:
  %.4 = icmp eq ptr %.1, null
  br i1 %.4, label %common.ret, label %.3.endif, !prof !6

common.ret:                                       ; preds = %.3.endif, %.3
  ret void

.3.endif:                                         ; preds = %.3
  %.4.i = atomicrmw add ptr %.1, i64 1 monotonic, align 8
  br label %common.ret
}

; Function Attrs: noinline
define linkonce_odr void @NRT_decref(ptr %.1) local_unnamed_addr #3 {
.3:
  %.4 = icmp eq ptr %.1, null
  br i1 %.4, label %common.ret1, label %.3.endif, !prof !6

common.ret1:                                      ; preds = %.3, %.3.endif
  ret void

.3.endif:                                         ; preds = %.3
  fence release
  %0 = tail call i8 @llvm.x86.atomic.sub.cc.i64(ptr nonnull %.1, i64 1, i32 4)
  %1 = trunc i8 %0 to i1
  br i1 %1, label %.3.endif.if, label %common.ret1, !prof !6

.3.endif.if:                                      ; preds = %.3.endif
  fence acquire
  tail call void @NRT_MemInfo_call_dtor(ptr nonnull %.1)
  ret void
}

; Function Attrs: nounwind
declare i8 @llvm.x86.atomic.sub.cc.i64(ptr, i64, i32 immarg) #4

declare void @NRT_MemInfo_call_dtor(ptr) local_unnamed_addr

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.ctlz.i64(i64, i1 immarg) #5

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.vector.reduce.add.v4i64(<4 x i64>) #5

attributes #0 = { mustprogress nocallback nofree nounwind willreturn memory(argmem: write) }
attributes #1 = { mustprogress nocallback nocreateundeforpoison nofree nosync nounwind speculatable willreturn memory(none) }
attributes #2 = { mustprogress nofree noinline norecurse nounwind willreturn memory(argmem: readwrite) }
attributes #3 = { noinline }
attributes #4 = { nounwind }
attributes #5 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!0 = distinct !{!0, !1, !2}
!1 = !{!"llvm.loop.isvectorized", i32 1}
!2 = !{!"llvm.loop.unroll.runtime.disable"}
!3 = !{!"branch_weights", i32 4, i32 12}
!4 = distinct !{!4, !1, !2}
!5 = distinct !{!5, !2, !1}
!6 = !{!"branch_weights", i32 1, i32 99}
!7 = !{!"branch_weights", i32 49, i32 1}
